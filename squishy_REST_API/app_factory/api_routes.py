"""
Routes module for REST API package.

This module defines the API routes and registers them with the Flask application.
"""
from flask import jsonify, request, Flask

from squishy_REST_API import logger, config


def register_api_routes(app: Flask, db_instance):
    """
    Register API routes with the Flask application.

    Args:
        app: Flask application instance
        db_instance: The DBConnection instance to use for API requests
    """
    # db_instance = db_instance

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

            return jsonify({"message": "Success", 'data': True})

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

    @app.route('/api/logs', methods=['GET', 'POST', 'DELETE'])
    def handle_logs():
        """Handle log operations - POST to add logs, GET to consolidate logs, DELETE to remove logs."""
        if request.method == 'POST':
            if 'summary_message' not in request.json.keys():
                logger.warning("POST /api/logs missing required 'summary_message' field")
                return jsonify({"message": "message required but not found in your request json"}), 400

            # Update site_id if unknown or 'local'
            if not request.json.get('site_id') or request.json.get('site_id').lower() == 'local':
                request.json['site_id'] = config.get('site_name')  # site_name is required to boot

            logger.debug(f"POST /api/logs")

            # Insert log entry
            if not (db_instance.put_log(request.json)):
                logger.error(f"Database error adding log entry")
                return jsonify({"message": "Database error, see DB logs"}), 500

            return jsonify({"message": "Success", 'data': True})

        elif request.method == 'GET':
            # Handle GET request for log consolidation
            action = request.args.get('action')
            if action in ['consolidate', 'shippable', 'older_than']:
                try:
                    success = False
                    if action == 'shippable':
                        logger.info("GET /api/logs?action=shippable - Starting log collection")
                        # Trigger log collection
                        success = db_instance.get_logs(session_id_filter='null')  # Returns data or false

                    if action == 'older_than':
                        logger.info("GET /api/logs?action=older_than - Starting log collection")
                        if request.args.get('days') and isinstance(request.args.get('days'), int):
                            # Trigger log collection
                            success = db_instance.get_logs(older_than_days=request.args.get('days'))  # Returns data or false

                    if action == 'consolidate':
                        logger.info("GET /api/logs?action=consolidate - Starting log consolidation")
                        # Trigger log consolidation
                        success = db_instance.consolidate_logs()  # Returns bool for success/failure

                    if success:
                        logger.info("Log operation completed successfully")
                        return jsonify({
                            "message": "Log operation completed successfully",
                            "data": success
                        }), 200
                    else:
                        logger.error("Log operation failed")
                        return jsonify({
                            "message": "Log operation failed",
                            "data": False
                        }), 500
                except Exception as e:
                    logger.error(f"Error during log operation: {e}", exc_info=True)
                    return jsonify({
                        "message": "Internal server error during log operation",
                        "data": False
                    }), 500
            else:
                # Handle other GET requests or missing action parameter
                logger.warning(f"GET /api/logs called without valid action parameter. Action: {action}")
                return jsonify({
                    "message": "Invalid or missing 'action' parameter. Use 'action=consolidate' to consolidate logs.",
                    "data": False
                }), 400

        elif request.method == 'DELETE':
            # Handle DELETE request for log deletion
            if not request.json:
                logger.warning("DELETE /api/logs missing request body")
                return jsonify({"message": "Request body required for DELETE operation"}), 400

            log_ids = request.json.get('log_ids')

            # Validate input
            if not log_ids:
                logger.warning("DELETE /api/logs missing 'log_ids' field")
                return jsonify({"message": "'log_ids' field required"}), 400

            if not isinstance(log_ids, list):
                logger.warning("DELETE /api/logs 'log_ids' must be a list")
                return jsonify({"message": "'log_ids' must be a list of integers"}), 400

            if not log_ids:
                logger.warning("DELETE /api/logs empty 'log_ids' list")
                return jsonify({"message": "'log_ids' cannot be empty"}), 400

            # Validate all IDs are integers
            try:
                log_ids = [int(log_id) for log_id in log_ids]
            except (ValueError, TypeError):
                logger.warning("DELETE /api/logs invalid log_ids format")
                return jsonify({"message": "All log IDs must be integers"}), 400

            logger.info(f"DELETE /api/logs attempting to delete {len(log_ids)} log entries")

            try:
                deleted_count = 0
                failed_deletes = []

                for log_id in log_ids:
                    result = db_instance.delete_log_entry(log_id)
                    if result:
                        deleted_count += 1
                    else:
                        failed_deletes.append(log_id)

                if failed_deletes:
                    logger.warning(f"Failed to delete log entries: {failed_deletes}")
                    return jsonify({
                        "message": f"Deleted {deleted_count} entries, failed to delete {len(failed_deletes)} entries",
                        "data": {
                            "deleted_count": deleted_count,
                            "failed_deletes": failed_deletes
                        }
                    }), 207  # 207 Multi-Status for partial success
                else:
                    logger.info(f"Successfully deleted {deleted_count} log entries")
                    return jsonify({
                        "message": f"Successfully deleted {deleted_count} log entries",
                        "data": {
                            "deleted_count": deleted_count
                        }
                    }), 200

            except Exception as e:
                logger.error(f"Error during log deletion: {e}", exc_info=True)
                return jsonify({
                    "message": "Internal server error during log deletion",
                    "data": False
                }), 500

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
