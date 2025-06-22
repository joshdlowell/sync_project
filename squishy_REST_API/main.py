"""
Main entry point for REST API package.

This module creates and runs the Flask application.
"""
from squishy_REST_API.app_factory import create_app
from squishy_REST_API.app_factory.logging_config import logger
from squishy_REST_API.config import config


def main():
    """Create and run the Flask application."""
    # Create application
    app = create_app()
    
    # Get configuration
    host = config.get('api_host', '0.0.0.0')
    port = config.get('api_port', 5000)
    debug = config.get('debug', False)
    
    # Run application
    logger.info(f"Starting application on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()