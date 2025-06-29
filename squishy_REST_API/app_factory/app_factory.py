"""
Application factory for REST API package.

This module provides a factory function to create Flask application instances
with proper configuration and dependency injection.
"""
from flask import Flask

from squishy_REST_API import config, logger
from squishy_REST_API.database_client import DBClient
from .api_routes import register_routes


class RESTAPIFactory:
    """Factory for creating rest api app"""

    @staticmethod
    def create_app(test_config=None):
        """
        Create and configure a Flask application instance.

        Args:
            db_instance: The DBConnection instance to use for API requests
            test_config: Optional configuration dictionary for testing

        Returns:
            Configured Flask application
        """
        # Get db instance
        db_instance = (DBClient()).database_client
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
            })
            logger.info("Application configured with default configuration")

        # Register routes
        register_routes(app, db_instance)

        # Log application startup
        logger.info(f"Application created with DEBUG={app.config['DEBUG']}")

        return app