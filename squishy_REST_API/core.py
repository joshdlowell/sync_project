# """
# Main entry point for REST API package.
#
# This module creates and runs the Flask application.
# """
# from squishy_REST_API.configuration import config
# from squishy_REST_API.app_factory import create_app
# from squishy_REST_API.configuration.logging_config import logger
#
#
# def main():
#     """Create and run the Flask application."""
#     # Create application
#     app = create_app()
#
#     # Get configuration
#     host = config.get('api_host')
#     port = config.get('api_port')
#     debug = config.get('debug')
#
#     # Run application
#     logger.info(f"Starting application on {host}:{port} (debug={debug})")
#     app.run(host=host, port=port, debug=debug)
#
#
# if __name__ == '__main__':
#     main()
"""
Main entry point for the squishy_REST_API package.
"""
import sys
import os
from squishy_REST_API.app_factory import create_app
# from squishy_REST_API.configuration.logging_config import logger
from squishy_REST_API import config, logger

# Create application instance for WSGI (at module level for Gunicorn)
app = create_app()


def run_with_gunicorn():
    """Run the application with Gunicorn."""
    try:
        from gunicorn.app.wsgiapp import WSGIApplication
    except ImportError:
        logger.error("Gunicorn not installed. Install with: pip install gunicorn")
        return False

    # Get configuration (config validation handled in config.py)
    gunicorn_config = config.gunicorn_config

    logger.info(f"Starting Gunicorn server on {gunicorn_config['bind']} with {gunicorn_config['workers']} workers")

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
    try:
        if config.get('use_gunicorn', True):
            if not run_with_gunicorn():
                logger.warning("Failed to start Gunicorn, falling back to development server")
                run_development()
        else:
            run_development()

    except Exception as e:
        logger.error(f"Fatal error in main routine: {e}")
        return 1  # Failure
    logger.info(f"REST_API server successfully started.")
    return 0 # Success


if __name__ == '__main__':
    main()