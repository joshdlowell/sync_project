To run your Flask app with Gunicorn instead of the built-in Flask development server, you'll need to make a few changes:

## 1. Modify your `main.py` file

```python
"""
Main entry point for REST API package.

This module creates the Flask application for WSGI deployment.
"""
from squishy_REST_API.app_factory.app_factory import create_app
from squishy_REST_API.configuration.logging_config import logger
from squishy_REST_API.configuration.config import config

# Create application instance for WSGI
app = create_app()


def main():
    """Create and run the Flask application with development server."""
    # Get configuration
    host = config.get('api_host', '0.0.0.0')
    port = config.get('api_port', 5000)
    debug = config.get('debug', False)

    # Run application (only for development)
    logger.info(f"Starting development server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
```

The key change is moving `app = create_app()` to the module level so Gunicorn can access it directly.

## 2. Install Gunicorn

```bash
pip install gunicorn
```

## 3. Launch with Gunicorn

You have several options for launching:

### Basic command:
```bash
gunicorn main:app
```

### With configuration options:
```bash
gunicorn main:app \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class sync \
    --timeout 30 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --log-level info
```

### Using environment variables from your config:
```bash
# If your config provides these values
gunicorn main:app \
    --bind $(python -c "from squishy_REST_API.config import config; print(f\"{config.get('api_host', '0.0.0.0')}:{config.get('api_port', 5000)}\")")
```

## 4. Optional: Create a Gunicorn configuration file

Create `gunicorn.conf.py`:

```python
"""Gunicorn configuration file."""
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

# Restart workers after this many requests, with up to this much jitter
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = 'info'
accesslog = '-'  # Log to stdout
errorlog = '-'  # Log to stderr

# Process naming
proc_name = 'squishy_rest_api'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None
```

Then launch with:
```bash
gunicorn main:app -c gunicorn.conf.py
```

## 5. Optional: Update your app factory for production settings

You might want to modify `create_app()` to handle production-specific settings:

```python
def create_app(test_config=None):
    """
    Create and configure a Flask application instance.
    
    Args:
        test_config: Optional configuration dictionary for testing
        
    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if test_config:
        # Load test configuration if provided
        app.config.update(test_config)
        logger.info("Application configured with test configuration")
    else:
        # Load configuration from config module
        app.config.update({
            'DEBUG': config.get('debug', False),
            'TESTING': False,
            'SECRET_KEY': config.get('secret_key', 'dev-key-change-in-production'),
            # Add production-specific settings
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': False,
        })
        logger.info("Application configured with default configuration")

    # Disable Flask's development server warning in production
    if not app.config['DEBUG']:
        import logging
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Register routes
    from squishy_REST_API.app_factory.api_routes import register_api_routes
    register_api_routes(app)

    # Log application startup
    logger.info(f"Application created with DEBUG={app.config['DEBUG']}")

    return app
```

## Summary of Changes:

1. **Module-level app creation**: Move `app = create_app()` outside the `main()` function
2. **Keep development option**: The `main()` function can still be used for development
3. **Gunicorn command**: Use `gunicorn main:app` instead of `python main.py`
4. **Configuration**: Optionally create a Gunicorn config file for easier management

This approach gives you flexibility to run either the development server (`python main.py`) or the production server (`gunicorn main:app`) as needed.

# ANSWER 2
If your `main.py` file is located at `/squishy_REST_API/main.py` (inside the package), the Gunicorn command changes depending on how you want to run it:

## Option 1: Run from the parent directory of the package

If your directory structure looks like this:
```
project_root/
├── squishy_REST_API/
│   ├── __init__.py
│   ├── main.py
│   ├── app_factory/
│   │   ├── __init__.py
│   │   ├── app_factory.py
│   │   └── ...
│   └── ...
```

Run from `project_root/`:
```bash
gunicorn squishy_REST_API.main:app
```

## Option 2: Run from within the package directory

If you're inside the `/squishy_REST_API/` directory:
```bash
cd squishy_REST_API
gunicorn main:app
```

## Option 3: Use absolute module path (recommended)

The most reliable approach is to ensure your package is properly installed or in the Python path, then use the full module path:

```bash
# If the package is installed
gunicorn squishy_REST_API.main:app

# Or if you need to add the parent directory to Python path
PYTHONPATH=/path/to/parent/directory gunicorn squishy_REST_API.main:app
```

## Option 4: Create a separate WSGI entry point (best practice)

Create a dedicated `wsgi.py` file in your project root:

```
project_root/
├── wsgi.py                    # <- New file
├── squishy_REST_API/
│   ├── __init__.py
│   ├── main.py
│   └── ...
```

**wsgi.py:**

```python
"""
WSGI entry point for the REST API application.
"""
from squishy_REST_API.core import app

if __name__ == "__main__":
    app.run()
```

Then run:
```bash
gunicorn wsgi:app
```

## Complete example commands:

### With configuration options:
```bash
# From project root
gunicorn squishy_REST_API.main:app \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class sync \
    --timeout 30 \
    --log-level info

# Or with separate wsgi.py
gunicorn wsgi:app \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --worker-class sync \
    --timeout 30 \
    --log-level info
```

### With config file:
```bash
gunicorn squishy_REST_API.main:app -c gunicorn.conf.py
```

## If you get import errors:

You might need to ensure your package structure is correct and the parent directory is in the Python path:

```bash
# Set PYTHONPATH explicitly
export PYTHONPATH=/path/to/project/root:$PYTHONPATH
gunicorn squishy_REST_API.main:app

# Or use python -m (if your package has proper __main__.py)
python -m gunicorn squishy_REST_API.main:app
```

## Recommended approach:

I'd suggest **Option 4** (separate `wsgi.py` file) as it's the cleanest and most conventional approach for production deployments. It keeps your application code separate from the WSGI entry point and makes deployment configurations clearer.