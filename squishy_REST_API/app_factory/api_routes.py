"""
Routes module for REST API package.

This module defines the API routes and registers them with the Flask application.
"""
from flask import jsonify, request, Flask

from squishy_REST_API import logger


def register_routes(app: Flask, db_instance):
    """
    Register API routes with the Flask application.

    Args:
        app: Flask application instance
        db_instance: The DBConnection instance to use for API requests
    """

    @app.route('/api/hashtable', methods=['GET', 'POST'])
    def get_put_hashes():
        """
        Get or update hash records.

        GET: Retrieve a hash record by path
        POST: Insert or update a hash record
        """
        if request.method == 'GET':
            path = request.args.get('path')
            logger.debug(f"GET /api/hashtable for path: {path}")
            if not path:
                logger.warning("GET /api/hashtable missing required 'path' parameter")
                return jsonify({"message": "path parameter is required"}), 400

            record = db_instance.get_hash_record(path)
            if not record:
                logger.info(f"Path not found: {path}")
                return jsonify({"message": "Path not found"}), 404
            else:
                return jsonify({"message": "Success", "data": record})

        elif request.method == 'POST':
            if 'path' not in request.json.keys():
                logger.warning("POST /api/hashtable missing required 'path' field")
                return jsonify({"message": "path required but not found in your request json"}), 400

            logger.debug(f"POST /api/hashtable for path: {request.json.get('path')}")
            logger.debug(f"request.json: {request.json}")

            # Insert or update hash
            if not db_instance.insert_or_update_hash(record=request.json):
                logger.error(f"Database error for record: {request.json}")
                return jsonify({"message": "Database error, see DB logs"}), 500

            return jsonify({"message": "Success"})

        else:
            logger.warning(f"Method not allowed: {request.method}")
            return jsonify({"message": f"'{request.method}' Method not allowed"}), 405

    @app.route('/api/hash', methods=['GET'])
    def get_hash():
        """Get a single hash value for a path."""
        path = request.args.get('path')
        logger.debug(f"GET /api/hash for path: {path}")

        hash_value = db_instance.get_single_hash_record(path)
        if not hash_value:
            logger.info(f"Path not found: {path}")
            return jsonify({"message": "Path not found"}), 404

        return jsonify({"message": "Success", "data": hash_value})

    @app.route('/api/timestamp', methods=['GET'])
    def get_timestamp():
        """Get the latest timestamp for a path."""
        path = request.args.get('path')
        logger.debug(f"GET /api/timestamp for path: {path}")

        record = db_instance.get_single_timestamp(path)
        if not record:
            logger.info(f"Path not found: {path}")
            return jsonify({"message": "Path not found"}), 404

        return jsonify({"message": "Success", "data": record}), 200

    @app.route('/api/priority', methods=['GET'])
    def get_priority():
        """
        Get a list of directories that need to be updated based on their age.

        Query parameters:
            root_path: The root directory to start from (required)
            percent: The percentage of directories to return (optional, default: 10)
        """
        logger.debug(f"GET /api/priority")

        # Get oldest updates from database
        priority = db_instance.get_priority_updates()

        return jsonify({"message": "Success", "data": priority}), 200

    @app.route('/api/lifecheck', methods=['GET'])
    def life_check():
        """Get the liveness of the api and database."""
        logger.debug(f"GET /api/lifecheck")
        return jsonify({"message": "Success",
                        "data": {'api': True,
                                 'db': db_instance.life_check()}}), 200

    @app.route('/api/logs', methods=['GET'])
    def put_logs():
        """Put a log entry in the database."""
        if request.method == 'POST':
            if 'summary_message' not in request.json.keys():
                logger.warning("POST /api/logs missing required 'summary_message' field")
                return jsonify({"message": "message required but not found in your request json"}), 400

            logger.debug(f"POST /api/logs")

            # Insert log entry
            if not (db_instance.put_log_entry(record=request.json)):
                logger.error(f"Database error adding log entry")
                return jsonify({"message": "Database error, see DB logs"}), 500

            return jsonify({"message": "Success", 'data': 0})

        else:
            logger.warning(f"Method not allowed: {request.method}")
            return jsonify({"message": f"'{request.method}' Method not allowed"}), 405

    # Register error handlers
    register_error_handlers(app)

    logger.info("API routes registered")


def register_error_handlers(app: Flask):
    """
    Register error handlers with the Flask application.

    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        logger.info(f"404 error: {error}")
        return jsonify({"message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"500 error: {error}")
        return jsonify({"message": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        return jsonify({"message": "Internal server error"}), 500
