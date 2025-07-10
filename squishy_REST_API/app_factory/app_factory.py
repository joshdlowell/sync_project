"""
Application factory for REST API package.

This module provides a factory function to create Flask application instances
with proper configuration and dependency injection.
"""
from flask import Flask
from flask_moment import Moment
from database_client import DBClientFactory

from squishy_REST_API import config, logger
from ..routes import register_all_routes
from .db_client_implementation import DBInstance


class RESTAPIFactory:
    """Factory for creating rest api app"""

    @staticmethod
    def create_app(test_config=None):
        """
        Create and configure a Flask application instance.
        Args:
            test_config: Optional configuration dictionary for testing
        Returns:
            Configured Flask application
        """

        # Get db instance for use in routes - database interactions
        db_config = {'database': config.database_config}
        db_client = DBClientFactory(db_config).create_client()
        db_instance = DBInstance(db_client)

        if config.is_core:  # Create Flask app (with locations of web-gui templates)
            app = Flask(__name__, template_folder='../web/templates', static_folder='../web/static')
            moment = Moment(app)  # Used in web-gui templates
        else:  # Create Flask app for remote site
            app = Flask(__name__)

        # Load configuration
        if test_config:
            if test_config.get('db_instance'):
                db_instance = test_config.pop('db_instance')
            app.config.update(test_config)  # Load test configuration if provided
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
        register_all_routes(app, db_instance, config.is_core)

        # Log application startup
        summary_message = f"REST API started at {config.site_name}. "
        detailed_message = f"DEBUG={app.config['DEBUG']}, Local API=True, Core API={config.is_core}"
        logger.info(summary_message + detailed_message)
        db_instance.put_log({'summary_message': summary_message, 'detailed_message': detailed_message})

        return app