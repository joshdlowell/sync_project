"""
data validation module for REST API package.

This module defines standard validation methods used across all the routes.
"""
from flask import jsonify

from squishy_REST_API import logger


def create_success_response(data=None, message="Success", status_code=200):
    """Create a standardized success response."""
    response = {"message": message}
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code


def create_error_response(message, status_code=500, error_type="Error"):
    """Create a standardized error response."""
    logger.error(message)
    return jsonify({
        "error": error_type,
        "message": message,
        "status": status_code
    }), status_code