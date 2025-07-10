"""
Main entry point for the squishy_REST_API package.

This module creates and runs a default Flask application with gunicorn WSGI server.
"""
from squishy_REST_API import config, logger, RESTAPIFactory

# Create application instance for WSGI (at module level for Gunicorn)
# app = RESTAPIFactory.create_app()  # TODO test if putting into args changes if it works


def run_with_gunicorn(app):
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
        def __init__(self, class_app, options=None):
            self.options = options or {}
            self.application = class_app
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


def run_development(app):
    """Run with Flask development server."""
    host = config.get('api_host', '0.0.0.0')
    port = config.get('api_port', 5000)
    debug = config.get('debug', False)

    logger.info(f"Starting development server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)


def main():
    """Main entry point with server selection."""

    # Create the app
    app = RESTAPIFactory.create_app()
    try:
        if config.get('use_gunicorn', True):  # Default to using gunicorn WSGI
            if not run_with_gunicorn(app):
                logger.warning("Failed to start Gunicorn, falling back to development server")
                run_development(app)
        else:
            run_development(app)

    except Exception as e:
        logger.error(f"Fatal error in main routine: {e}")
        return 1  # Failure
    logger.info(f"REST_API server successfully started.")
    return 0 # Success


if __name__ == '__main__':
    main()