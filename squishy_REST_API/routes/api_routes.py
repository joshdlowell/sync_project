"""
Routes module for REST API package.

This module defines the basic API routes and registers them with the Flask application.
"""
from flask import jsonify, request, Flask
from datetime import datetime, timezone

from squishy_REST_API import logger, config
from .utils import create_success_response, create_error_response


def register_api_routes(app: Flask, db_instance):
    """
    Register API routes with the Flask application.

    Args:
        app: Flask application instance
        db_instance: The DBConnection instance to use for API requests
    """

    @app.route('/api/hashtable', methods=['GET', 'POST'])
    def hashtable_operations():
        """
        Get or update hash records.

        GET: Retrieve hash data by path with optional field selection
        POST: Insert or update a hash record
        """
        if request.method == 'GET':
            path = request.args.get('path')
            field = request.args.get('field', 'record')  # Default to full record

            logger.debug(f"GET /api/hashtable for path: {path}, field: {field}")

            try:
                if field == 'hash':
                    # Get only the hash value
                    result = db_instance.get_single_hash_record(path)
                    if not result:
                        return create_error_response(f"Path not found", 404)
                    return create_success_response(data=result)

                elif field == 'timestamp':
                    # Get only the timestamp
                    result = db_instance.get_single_timestamp(path)
                    if not result:
                        return create_error_response(f"Path not found", 404)
                    return create_success_response(data=result)

                elif field == 'record':
                    # Get full record (default behavior)
                    result = db_instance.get_hash_record(path)
                    if not result:
                        return create_error_response(f"Path not found", 404)
                    return create_success_response(data=result)

                elif field == 'priority':
                    # Get a list of paths that will ensure all out of sync hashes get updated
                    result = db_instance.get_priority_updates()
                    return create_success_response(data=result)

                elif field == 'untracked':
                    # Get a list of paths that parents claim, but aren't in the db
                    result = db_instance.find_untracked_children()
                    return create_success_response(data=result)

                elif field == 'orphaned':
                    # Get a list of paths that aren't reported by any parent
                    result = db_instance.find_orphaned_entries()
                    return create_success_response(data=result)

                else:
                    return create_error_response(f"Invalid field parameter. Use 'hash', 'timestamp', or 'record'", 400)

            except ValueError as e:
                return create_error_response(e, 400)

        elif request.method == 'POST':
            logger.debug(f"POST /api/hashtable for path: {request.json.get('path')}")
            try:
                # Insert or update hash
                response = db_instance.insert_or_update_hash(record=request.json)
                if not response:
                    logger.error(f"Database error for record: {request.json}")
                    return create_error_response("Database error, see DB logs", error_type='Database error')
                return create_success_response(data=response)
            except ValueError as e:
                return create_error_response(e, 400)

    # @app.route('/api/priority', methods=['GET'])
    # def get_priority():
    #     """Get a list of directories that need to be updated based on their hash values."""
    #     logger.debug(f"GET /api/priority")
    #     # Get a list of paths that will ensure all out of sync hashes get updated
    #     priority = db_instance.get_priority_updates()
    #     return create_success_response(data=priority)

    @app.route('/api/logs', methods=['GET', 'POST', 'DELETE'])
    def handle_logs():
        """Handle log operations - POST to add logs, GET to consolidate logs, DELETE to remove logs."""
        if request.method == 'POST':
            logger.debug(f"POST /api/logs")
            # Update site_id if unknown or 'local'
            if not request.json.get('site_id') or request.json.get('site_id').lower() == 'local':
                request.json['site_id'] = config.get('site_name')  # site_name is required to boot-up
            try: # Insert log entry
                response = db_instance.put_log(request.json)
                if not response:
                    return create_error_response("Error adding log entry")
            except ValueError as e:
                return create_error_response(e, 400)

            return create_success_response(data=True)

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
                        success = db_instance.consolidate_logs()

                    if success:
                        return create_success_response(data=success)
                    else:
                        return create_error_response("Error during log operation")
                except Exception as e:
                    logger.error(f"Error during log operation: {e}", exc_info=True)
                    return create_error_response(e)
            else:
                # Handle other GET requests or missing action parameter
                logger.warning(f"GET /api/logs called without valid action parameter. Action: {action}")
                return create_error_response("Invalid or missing 'action' parameter. Use 'action=consolidate' to consolidate logs.", status_code=400)

        elif request.method == 'DELETE':
            # Handle DELETE request for log deletion
            logger.debug(f"DELETE /api/logs")
            if not request.json:
                logger.warning("DELETE /api/logs missing request body")
                return create_error_response(message="Request body required for DELETE operation", status_code=400)

            try:
                deleted_count, failed_deletes = db_instance.delete_log_entries(request.json.get('log_ids'))

                if len(failed_deletes) > 0:
                    logger.warning(f"Failed to delete log entries: {failed_deletes}")
                    return create_success_response(message="Partial success",
                                                   data={
                                                       "deleted_count": deleted_count,
                                                       "failed_deletes": failed_deletes
                                                   },
                                                   status_code=207)  # 207 Multi-Status for partial success
                logger.info(f"Successfully deleted {deleted_count} log entries")
                return create_success_response(data={"deleted_count": deleted_count})
            except Exception as e:
                logger.error(f"Error during log deletion: {e}", exc_info=True)
                return create_error_response(e)
        return create_error_response("Invalid request method")

    # @app.route('/api/orphans', methods=['GET'])
    # def find_orphans():
    #     """Get all entries that aren't listed by a parent"""
    #     logger.debug(f"GET /api/orphans")
    #
    #     try:
    #         # Get oldest updates from database
    #         orphaned_paths = db_instance.find_orphaned_entries()
    #     except Exception as e:
    #         logger.error(f"Error during orphaned entry search: {e}", exc_info=True)
    #         return create_error_response(e)
    #
    #     logger.info(f"Found {len(orphaned_paths)} orphaned entries")
    #     return create_success_response(data=orphaned_paths)
    #
    # @app.route('/api/untracked', methods=['GET'])
    # def find_untracked():
    #     """Get a list of children claimed by a parent but not tracked in the database"""
    #     logger.debug(f"GET /api/untracked")
    #     try:
    #         # Get oldest updates from database
    #         untracked_paths = db_instance.find_untracked_children()
    #     except Exception as e:
    #         logger.error(f"Error during untracked child search: {e}", exc_info=True)
    #         return create_error_response(e)
    #
    #     logger.info(f"Found {len(untracked_paths)} untracked children")
    #     return create_success_response(data=untracked_paths)

    @app.route('/api/lifecheck', methods=['GET'])
    @app.route('/health', methods=['GET'])
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Get the liveness of the api and database."""
        logger.debug(f"GET /api/health")
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "site_name": config.get('site_name'),
            "services": {
                "api": True,
            }
        }
        # Get database(s) health status
        response = db_instance.health_check()
        for key, value in response.items():
            health_status["services"][key] = value

        if not all(health_status["services"].values()):
            health_status["status"] = "unhealthy"

        return create_success_response(data=health_status)

    @app.route('/api/docs')
    def api_documentation():
        """Return API documentation."""
        docs = {
            "version": "2.0",
            "endpoints": {
                "/api/hashtable": {
                    "methods": ["GET", "POST"],
                    "description": "Manage hash records",
                    "parameters": {
                        "GET": {"path": "string (required)"},
                        "POST": {"path": "string (required)", "...": "hash data"}
                    }
                },
                # ... other endpoints
            }
        }
        return jsonify(docs)

    logger.info("API routes registered")

