"""
Error handlers module for REST API package.

This module defines the error handlers used across all the routes
and registers them with the Flask application.
"""
from flask import jsonify, request, Flask, render_template

from squishy_REST_API import logger
from .utils import create_error_response

def register_error_handlers(app: Flask):
    """Register unified error handlers for both API and GUI routes."""

    @app.errorhandler(404)
    def handle_404_error(error):
        logger.info(f"404 error: {error}")
        if request.path.startswith('/api/'):
            return create_error_response(message="The requested API resource was not found.",
                                         status_code=404,
                                         error_type="Not Found")
        else:
            return render_template('error.html', error=f"Path not found: {error}"), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")

        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Method Not Allowed",
                "message": f"Method '{request.method}' not allowed for this endpoint",
                "status": 405,
                "allowed_methods": error.description if hasattr(error, 'description') else None
            }), 405
        else:
            return render_template('error.html',
                                   error=f"Method '{request.method}' not allowed"), 405

    @app.errorhandler(500)
    def handle_500_error(error):
        logger.error(f"500 error: {error}")
        if request.path.startswith('/api/'):
            return create_error_response(message="Internal server error",
                                         error_type="Server Error")
        else:
            return render_template('error.html', error=f"Internal server error: {error}"), 500


    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        if request.path.startswith('/api/'):
            return create_error_response(message="Internal server error",
                                         error_type="Server Error")
        else:
            return render_template('error.html', error=f"Internal server error: {error}"), 500