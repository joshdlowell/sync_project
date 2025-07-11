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
        """Return comprehensive API documentation."""

        # Base documentation structure
        docs = {
            "api_version": "2.0",
            "site_name": config.get('site_name'),
            "site_type": "core" if config.is_core else "remote",
            "description": "Squishy REST API - File hash tracking and synchronization system",
            "base_url": request.host_url.rstrip('/'),
            "endpoints": {}
        }

        # Core API endpoints (available on all sites)
        docs["endpoints"].update({
            "/api/hashtable": {
                "methods": ["GET", "POST"],
                "description": "Manage hash records for files and directories",
                "parameters": {
                    "GET": {
                        "path": {
                            "type": "string",
                            "required": True,
                            "description": "File or directory path to query"
                        },
                        "field": {
                            "type": "string",
                            "required": False,
                            "default": "record",
                            "options": ["record", "hash", "timestamp", "priority", "untracked", "orphaned"],
                            "description": "Specific field to retrieve"
                        }
                    },
                    "POST": {
                        "body": {
                            "type": "object",
                            "required": True,
                            "description": "Hash record data",
                            "example": {
                                "path": "/example/path",
                                "current_hash": "abc123...",
                                "current_dtg_latest": 1234567890,
                                "files": ["file1.txt", "file2.txt"],
                                "dirs": ["subdir1", "subdir2"],
                                "links": []
                            }
                        }
                    }
                },
                "responses": {
                    "200": "Success with requested data",
                    "400": "Invalid request parameters",
                    "404": "Path not found (GET only)",
                    "500": "Server error"
                }
            },
            "/api/logs": {
                "methods": ["GET", "POST", "DELETE"],
                "description": "Manage application logs",
                "parameters": {
                    "GET": {
                        "action": {
                            "type": "string",
                            "required": True,
                            "options": ["consolidate", "shippable", "older_than"],
                            "description": "Log operation to perform"
                        },
                        "days": {
                            "type": "integer",
                            "required": False,
                            "description": "Number of days (used with action=older_than)"
                        }
                    },
                    "POST": {
                        "body": {
                            "type": "object",
                            "required": True,
                            "description": "Log entry data",
                            "example": {
                                "site_id": "SITE1",
                                "log_level": "INFO",
                                "summary_message": "Operation completed",
                                "detailed_message": "Detailed log information"
                            }
                        }
                    },
                    "DELETE": {
                        "body": {
                            "type": "object",
                            "required": True,
                            "description": "Log IDs to delete",
                            "example": {
                                "log_ids": [1, 2, 3, 4, 5]
                            }
                        }
                    }
                },
                "responses": {
                    "200": "Success",
                    "207": "Partial success (DELETE only)",
                    "400": "Invalid request parameters",
                    "500": "Server error"
                }
            },
            "/api/health": {
                "methods": ["GET"],
                "description": "Health check endpoint for API and database services",
                "aliases": ["/health", "/api/lifecheck"],
                "responses": {
                    "200": "Health status information",
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "site_name": "SITE1",
                        "services": {
                            "api": True,
                            "database": True
                        }
                    }
                }
            },
            "/api/docs": {
                "methods": ["GET"],
                "description": "This endpoint - returns API documentation",
                "responses": {
                    "200": "API documentation in JSON format"
                }
            }
        })

        # Add core-specific endpoints if this is a core site
        if config.is_core:
            docs["endpoints"].update({
                "/api/pipeline": {
                    "methods": ["GET", "POST"],
                    "description": "Manage pipeline operations (core site only)",
                    "parameters": {
                        "GET": {
                            "action": {
                                "type": "string",
                                "required": False,
                                "default": "updates",
                                "options": ["updates", "sites"],
                                "description": "Type of pipeline data to retrieve"
                            }
                        },
                        "POST": {
                            "body": {
                                "type": "object",
                                "required": True,
                                "description": "Pipeline operation data",
                                "examples": {
                                    "hash_update": {
                                        "action": "hash",
                                        "update_path": "/example/path",
                                        "hash_value": "abc123..."
                                    },
                                    "site_status": {
                                        "action": "site_status",
                                        "site_name": "SITE1",
                                        "status_data": {"last_sync": 1234567890}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": "Success",
                        "400": "Invalid request parameters",
                        "501": "Operation not supported",
                        "503": "Pipeline database unavailable"
                    }
                }
            })

            # Add web GUI endpoints for core sites
            docs["web_endpoints"] = {
                "/": {
                    "methods": ["GET"],
                    "description": "Main dashboard (core site only)",
                    "aliases": ["/dashboard"]
                },
                "/web/hashtable/<path:file_path>": {
                    "methods": ["GET"],
                    "description": "Detailed view of hashtable record (core site only)"
                },
                "/web/liveness": {
                    "methods": ["GET"],
                    "description": "Site liveness status page (core site only)"
                },
                "/web/logs": {
                    "methods": ["GET"],
                    "description": "Logs viewing page with filtering (core site only)",
                    "parameters": {
                        "log_level": {
                            "type": "string",
                            "required": False,
                            "description": "Filter by log level"
                        },
                        "site_id": {
                            "type": "string",
                            "required": False,
                            "description": "Filter by site ID"
                        }
                    }
                },
                "/web/status": {
                    "methods": ["GET"],
                    "description": "Hash synchronization status page (core site only)"
                }
            }

        # Add authentication info if applicable
        if config.get('secret_key'):
            docs["authentication"] = {
                "type": "session-based",
                "description": "API uses Flask sessions for authentication"
            }

        # Add general information
        docs["general_info"] = {
            "error_format": {
                "structure": {
                    "error": "Error type",
                    "message": "Human readable error message",
                    "status": "HTTP status code"
                },
                "example": {
                    "error": "Not Found",
                    "message": "The requested API resource was not found.",
                    "status": 404
                }
            },
            "success_format": {
                "structure": {
                    "message": "Success message",
                    "data": "Response data (optional)"
                },
                "example": {
                    "message": "Success",
                    "data": {"result": "value"}
                }
            },
            "content_types": {
                "request": "application/json",
                "response": "application/json"
            }
        }

        return jsonify(docs)

    logger.info("API routes registered")

