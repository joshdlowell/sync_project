Yes, you can definitely incorporate Gunicorn configuration and have the app start natively with Gunicorn when using `python -m squishy_REST_API`. Here are a few approaches:

## Option 1: Modify `__main__.py` to detect and use Gunicorn

Update your `squishy_REST_API/__main__.py`:

```python
"""
Main entry point for the squishy_REST_API package.
"""
import sys
import os
from squishy_REST_API.app_factory.app_factory import create_app
from squishy_REST_API.configuration.logging_config import logger
from squishy_REST_API.configuration.config import config

# Create application instance for WSGI (at module level for Gunicorn)
app = create_app()

def run_with_gunicorn():
    """Run the application with Gunicorn."""
    try:
        from gunicorn.app.wsgiapp import WSGIApplication
    except ImportError:
        logger.error("Gunicorn not installed. Install with: pip install gunicorn")
        return False
    
    # Get configuration
    host = config.get('api_host', '0.0.0.0')
    port = config.get('api_port', 5000)
    workers = config.get('gunicorn_workers', 4)
    
    # Gunicorn configuration
    gunicorn_config = {
        'bind': f'{host}:{port}',
        'workers': workers,
        'worker_class': 'sync',
        'timeout': 30,
        'keepalive': 2,
        'max_requests': 1000,
        'max_requests_jitter': 100,
        'loglevel': 'info',
        'accesslog': '-',
        'errorlog': '-',
        'proc_name': 'squishy_rest_api'
    }
    
    logger.info(f"Starting Gunicorn server on {host}:{port} with {workers} workers")
    
    # Create Gunicorn app
    class StandaloneApplication(WSGIApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    # Run with Gunicorn
    StandaloneApplication(app, gunicorn_config).run()
    return True

def run_development():
    """Run with Flask development server."""
    host = config.get('api_host', '0.0.0.0')
    port = config.get('api_port', 5000)
    debug = config.get('debug', False)
    
    logger.info(f"Starting development server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point with server selection."""
    # Check for command line arguments
    use_gunicorn = '--gunicorn' in sys.argv or config.get('use_gunicorn', False)
    
    if use_gunicorn:
        if not run_with_gunicorn():
            logger.warning("Failed to start Gunicorn, falling back to development server")
            run_development()
    else:
        run_development()

if __name__ == '__main__':
    main()
```

## Option 2: Add Gunicorn Config File and Command Line Options

Create `squishy_REST_API/gunicorn_config.py`:

```python
"""Gunicorn configuration for squishy_REST_API."""
from squishy_REST_API.configuration.config import config

# Server socket
bind = f"{config.get('api_host', '0.0.0.0')}:{config.get('api_port', 5000)}"
backlog = 2048

# Worker processes
workers = config.get('gunicorn_workers', 4)
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after requests
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = 'info'
accesslog = '-'
errorlog = '-'

# Process naming
proc_name = 'squishy_rest_api'

# Server mechanics
daemon = False
preload_app = True
```

Update `__main__.py` with argument parsing:

```python
"""
Main entry point for the squishy_REST_API package.
"""
import sys
import argparse
import os
from pathlib import Path
from squishy_REST_API.app_factory.app_factory import create_app
from squishy_REST_API.configuration.logging_config import logger
from squishy_REST_API.configuration.config import config

# Create application instance for WSGI
app = create_app()

def get_gunicorn_config_path():
    """Get path to gunicorn config file."""
    return Path(__file__).parent / 'gunicorn_config.py'

def run_with_gunicorn():
    """Run with Gunicorn using subprocess."""
    import subprocess
    
    config_path = get_gunicorn_config_path()
    module_path = f"{__package__}.__main__:app"
    
    cmd = [
        'gunicorn',
        module_path,
        '-c', str(config_path)
    ]
    
    logger.info(f"Starting Gunicorn with command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Gunicorn failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        logger.error("Gunicorn not found. Install with: pip install gunicorn")
        return False
    
    return True

def run_development():
    """Run with Flask development server."""
    host = config.get('api_host', '0.0.0.0')
    port = config.get('api_port', 5000)
    debug = config.get('debug', False)
    
    logger.info(f"Starting development server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Run squishy REST API')
    parser.add_argument('--gunicorn', action='store_true', 
                       help='Run with Gunicorn production server')
    parser.add_argument('--dev', action='store_true', 
                       help='Run with Flask development server (default)')
    
    args = parser.parse_args()
    
    # Determine which server to use
    use_gunicorn = args.gunicorn or config.get('use_gunicorn', False)
    
    if use_gunicorn:
        if not run_with_gunicorn():
            logger.warning("Failed to start Gunicorn, falling back to development server")
            run_development()
    else:
        run_development()

if __name__ == '__main__':
    main()
```

## Option 3: Environment Variable Control

Add to your config system to check for environment variables:

```python
# In your configuration/config.py
import os

# Add to your config loading
config.update({
    'use_gunicorn': os.getenv('SQUISHY_USE_GUNICORN', 'false').lower() == 'true',
    'gunicorn_workers': int(os.getenv('SQUISHY_GUNICORN_WORKERS', '4')),
})
```

## Usage Examples:

With Option 1 or 2:
```bash
# Run with development server (default)
python -m squishy_REST_API

# Run with Gunicorn
python -m squishy_REST_API --gunicorn

# Force development server
python -m squishy_REST_API --dev
```

With environment variables:
```bash
# Run with Gunicorn via environment variable
SQUISHY_USE_GUNICORN=true python -m squishy_REST_API

# Set worker count
SQUISHY_GUNICORN_WORKERS=8 SQUISHY_USE_GUNICORN=true python -m squishy_REST_API
```

## Option 4: Pure Gunicorn Integration (Recommended)

Create a separate entry point for production while keeping development simple:

**squishy_REST_API/wsgi.py:**
```python
"""WSGI entry point for production deployment."""
from squishy_REST_API.app_factory.app_factory import create_app

# Create app instance for WSGI servers
application = create_app()
app = application  # Alias for compatibility
```

Then you can run:
```bash
# Development
python -m squishy_REST_API

# Production with Gunicorn
gunicorn squishy_REST_API.wsgi:app -c squishy_REST_API/gunicorn_config.py
```

**Option 2** is probably the most flexible, giving you both the convenience of `python -m squishy_REST_API --gunicorn` and the ability to fall back to development mode easily.