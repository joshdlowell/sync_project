"""
data validation module for REST API package.

This module defines standard validation methods used across all the routes.
"""
from flask import jsonify

from squishy_REST_API import logger

# Moved all values error handling to the db implementation for easier updating
# def validate_required_fields(data, required_fields):
#     """Validate that required fields are present in the data."""
#     missing_fields = []
#     for field in required_fields:
#         if field not in data or not data[field]:
#             missing_fields.append(field)
#
#     if missing_fields:
#         return False, f"Missing required fields: {', '.join(missing_fields)}"
#     return True, None
#
#
# def validate_path_parameter(path):
#     """Validate path parameter."""
#     if not path:
#         logger.error("Missing required 'path' parameter")
#         return False, None, "path parameter is required"
#     if not isinstance(path, str):
#         logger.error("'path' parameter must be a string")
#         return False, None, "path must be a string"
#     return True, path, None


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