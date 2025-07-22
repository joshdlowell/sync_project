"""
Core Routes module for REST API package.

This module defines the API routes necessary for core site operations and registers them with the Flask application.
"""
from flask import jsonify, request, Flask, render_template

from squishy_REST_API import logger, config
from .utils import create_success_response, create_error_response


def register_core_routes(app: Flask, db_instance):
    """Register core routes with the Flask application."""

    @app.route('/api/pipeline', methods=['GET', 'POST'])
    def handle_pipeline():
        """
        Handle pipeline operations.

        GET: Retrieve pipeline updates or official sites list
        POST: Update pipeline hash or post remote site hash status
        """
        # Check if pipeline database instance is available upfront
        if not hasattr(db_instance, 'get_pipeline_updates'):
            logger.error("Pipeline database instance not available")
            return create_error_response(message="Pipeline database instance not available", status_code=503)

        if request.method == 'GET':
            action = request.args.get('action', 'updates')  # Default to 'updates' if no action specified

            if action == 'updates':
                logger.debug(f"GET /api/pipeline?action=updates")
                try:
                    pipeline_updates = db_instance.get_pipeline_updates()
                    logger.info(f"Found {len(pipeline_updates)} unprocessed updates")
                    return create_success_response(data=pipeline_updates)
                except Exception as e:
                    logger.error(f"Error getting pipeline updates: {e}")
                    return create_error_response(e)

            elif action == 'sites':
                logger.debug(f"GET /api/pipeline?action=sites")
                try:
                    success = db_instance.sync_sites_from_mssql_upsert(db_instance.get_pipeline_sites())
                    logger.info(f"{'Success synchronizing' if success else 'Failed to sync'} sites table")
                    return create_success_response(data=success)
                except Exception as e:
                    logger.error(f"Error getting official sites: {e}")
                    return create_error_response(e)

            else:
                logger.warning(f"GET /api/pipeline called with invalid action: {action}")
                return create_error_response(
                    message="Invalid 'action' parameter. Use 'action=updates' or 'action=sites'",
                    status_code=400
                )

        elif request.method == 'POST':
            if not request.json:
                logger.warning("POST /api/pipeline missing request body")
                return create_error_response(message="Request body required for POST operation", status_code=400)

            action = request.json.get('action')

            if action == 'hash':
                logger.debug(f"POST /api/pipeline action=hash for path: {request.json.get('update_path')}")
                try:
                    update_path = request.json.get('update_path')
                    hash_value = request.json.get('hash_value')

                    if not update_path or not hash_value:
                        return create_error_response(
                            message="Both 'update_path' and 'hash_value' are required for hash updates",
                            status_code=400
                        )

                    success = db_instance.put_pipeline_hash(update_path, hash_value)
                    if success:
                        logger.info(f"Successfully updated pipeline hash for path: {update_path}")
                        return create_success_response(data=True)
                    else:
                        logger.error(f"Failed to update pipeline hash for path: {update_path}")
                        return create_error_response(
                            message="Failed to update pipeline hash",
                            error_type='Database error'
                        )
                except ValueError as e:
                    return create_error_response(e, 400)
                except Exception as e:
                    logger.error(f"Error updating pipeline hash: {e}")
                    return create_error_response(e)

            elif action == 'site_status':
                logger.debug(f"POST /api/pipeline action=site_status for site: {request.json.get('site_name')}")
                try:
                    # This would be for posting remote site hash status to local database
                    site_name = request.json.get('site_name')
                    status_data = request.json.get('status_data')

                    if not site_name or not status_data:
                        return create_error_response(
                            message="Both 'site_name' and 'status_data' are required for site status updates",
                            status_code=400
                        )

                    # Assuming you'll add a method like put_remote_site_status to your local db
                    if hasattr(db_instance, 'put_remote_site_status'):
                        success = db_instance.put_remote_site_status(site_name, status_data)
                        if success:
                            logger.info(f"Successfully updated site status for: {site_name}")
                            return create_success_response(data=True)
                        else:
                            logger.error(f"Failed to update site status for: {site_name}")
                            return create_error_response(
                                message="Failed to update site status",
                                error_type='Database error'
                            )
                    else:
                        logger.error("Local database instance doesn't support remote site status updates")
                        return create_error_response(
                            message="Remote site status updates not supported",
                            status_code=501
                        )
                except ValueError as e:
                    return create_error_response(e, 400)
                except Exception as e:
                    logger.error(f"Error updating site status: {e}")
                    return create_error_response(e)

            else:
                logger.warning(f"POST /api/pipeline called with invalid action: {action}")
                return create_error_response(
                    message="Invalid 'action' parameter. Use 'action=hash' or 'action=site_status'",
                    status_code=400
                )

        return create_error_response("Invalid request method")

    @app.route('/api/remote_status', methods=['POST'])
    def handle_remote_status():
        """
        Handle remote site status operations.

        POST: Update out of sync hash status for a remote site
        """
        if request.method == 'POST':
            if not request.json:
                logger.warning("POST /api/remote_status missing request body")
                return create_error_response(message="Request body required for POST operation", status_code=400)

            action = request.json.get('action')

            if action == 'remote_updates':
                logger.debug(f"POST /api/pipeline action=remote_updates")
                try:
                    drop_previous = request.json.get('drop_previous', True)
                    site_name = request.json.get('site_name')
                    updates = request.json.get('updates')
                    root_path = request.json.get('root_path', None)

                    if not site_name or not updates or len(updates) == 0:
                        raise ValueError("site_name and updates required for site status updates")

                    updates_completed = db_instance.put_remote_hash_status(updates, site_name, drop_previous, root_path)

                    return create_success_response(data=updates_completed)

                except ValueError as e:
                    return create_error_response(e, 400)
                except Exception as e:
                    logger.error(f"Error updating pipeline hash: {e}")
                    return create_error_response(e)

            else:
                logger.warning(f"POST /api/remote_status called with invalid action: {action}")
                return create_error_response(
                    message="Invalid 'action' parameter. Use 'action=remote_updates'",
                    status_code=400
                )

        return create_error_response("Invalid request method")
