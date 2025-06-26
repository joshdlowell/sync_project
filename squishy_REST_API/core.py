"""
Main entry point for REST API package.

This module creates and runs the Flask application.
"""
from squishy_REST_API.configuration import config
from squishy_REST_API.app_factory import create_app
from squishy_REST_API.configuration.logging_config import logger


def main():
    """Create and run the Flask application."""
    # Create application
    app = create_app()  # Modify to pull config from imported
    
    # Get configuration
    host = config.get('api_host')
    port = config.get('api_port')
    debug = config.get('debug')
    
    # Run application
    logger.info(f"Starting application on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()