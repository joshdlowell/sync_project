"""
Routes module for REST API package.

This module defines the API routes and registers them with the Flask application.
"""
from flask import jsonify, request, Flask, render_template
from datetime import datetime, timezone

from squishy_REST_API import logger, config


def register_gui_routes(app: Flask, core_db_instance, db_instance):
    """
    Register web gui routes with the Flask application.

    Args:
        app: Flask application instance
        core_db_instance: The DBConnection instance to use for core site function web requests
        db_instance: The DBConnection instance to use for routine site web requests
    """

    @app.route('/')
    def dashboard():
        """Display the main dashboard with hashtable overview."""
        logger.debug("GET / - Dashboard request")

        try:
            # Get all dashboard metrics from the database
            dashboard_data = core_db_instance.get_dashboard_content()
            logger.debug(dashboard_data)
            return render_template('dashboard.html', dashboard_data=dashboard_data)

        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            return render_template('error.html', error="Failed to load dashboard"), 500

    @app.route('/web/hashtable/<path:file_path>')
    def web_hashtable_detail(file_path):
        """Display detailed view of a specific hashtable record."""
        logger.debug(f"GET /web/hashtable/{file_path} - HTML hashtable detail request")
        try:

            record = db_instance.get_hash_record(f"/{file_path}")

            if not record:
                logger.info(f"Path not found: {file_path}")
                return render_template('error.html', error=f"Path not found: {file_path}"), 404
            # Reformat data for display
            for key in ['current_dtg_latest', 'current_dtg_first', 'prev_dtg_latest']:
                if record.get(key):
                    record[key] = datetime.fromtimestamp(record[key], tz=timezone.utc)
                else:
                    record[key] = None
            logger.debug(f"Reformatted timestamps")
            # Reformat files dirs and links
            for key in ['files', 'dirs', 'links']:
                if not record.get(key):
                    record[key] = []
            logger.debug(f"Reformatted dirs files and links")
            return render_template('hashtable_detail.html',
                                   record=record,
                                   file_path=file_path)
        except Exception as e:
            logger.error(f"Error rendering hashtable detail: {e}")
            return render_template('error.html', error="Failed to load record details"), 500

    @app.route('/web/liveness')
    def site_liveness():
        """Display the liveness status of sites in the network."""
        logger.debug("GET / - site_liveness request")

        try:
            # Get all liveness metrics from the database
            liveness_data = core_db_instance.get_site_liveness()
            for row in liveness_data:
                if row['last_updated']:
                    row['last_updated'] = datetime.fromtimestamp(row['last_updated'], tz=timezone.utc)
                else:
                    row['last_updated'] = None


            return render_template('site_liveness.html', liveness_data=liveness_data)

        except Exception as e:
            logger.error(f"Error rendering site liveness: {e}")
            return render_template('error.html', error="Failed to load site liveness"), 500

    @app.route('/web/logs')
    def logs():
        """
        Display logs page with optional filtering by log_level and/or site_id.

        Query parameters:
            log_level: Filter logs by specific log level
            site_id: Filter logs by specific site ID
        """
        # Get filter parameters from query string
        requested_log_level = request.args.get('log_level', '').strip()
        requested_site_id = request.args.get('site_id', '').strip()

        # Get valid options for dropdowns
        valid_log_levels = config.VALID_LOG_LEVELS
        valid_site_ids = core_db_instance.get_valid_site_ids()

        # Validate and sanitize filters
        log_level_filter = None
        site_id_filter = None

        if requested_log_level and requested_log_level.upper() in [level.upper() for level in valid_log_levels]:
            log_level_filter = requested_log_level.upper()

        if requested_site_id and requested_site_id in valid_site_ids:
            site_id_filter = requested_site_id

        # Get filtered logs
        logs_data = core_db_instance.get_recent_logs(log_level=log_level_filter, site_id=site_id_filter)

        # Convert UNIX timestamps to datetime objects for template
        for log in logs_data:
            if log.get('timestamp'):
                log['formatted_timestamp'] = datetime.fromtimestamp(log['timestamp'], tz=timezone.utc)
            else:
                log['formatted_timestamp'] = None

        return render_template('logs.html',
                               logs=logs_data,
                               valid_log_levels=valid_log_levels,
                               valid_site_ids=valid_site_ids,
                               current_log_level=log_level_filter,
                               current_site_id=site_id_filter)

    @app.route('/web/status')
    def hash_status():
        """Display the hash status of sites in the network."""
        logger.debug("GET / - hash_status request")

        try:
            # Get all liveness metrics from the database
            hash_sync_data = core_db_instance.get_site_sync_status()
            for row in hash_sync_data:
                if row.get('last_updated'):
                    row['last_updated'] = datetime.fromtimestamp(row['last_updated'], tz=timezone.utc)
                else:
                    row['last_updated'] = None
            return render_template('hash_status.html', hash_sync_data=hash_sync_data)

        except Exception as e:
            logger.error(f"Error rendering hash_status: {e}")
            return render_template('error.html', error="Failed to load hash status"), 500

    register_error_handlers(app)

    logger.info("web-gui routes registered")


def register_error_handlers(app: Flask):
    """
    Register error handlers with the Flask application.

    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def handle_404_error(error):
        logger.info(f"404 error: {error}")
        # Check if the request is for the API
        if request.path.startswith('/api/'):  # The API base path

            response = {
                "error": "Not Found",
                "message": "The requested API resource was not found.",
                "status": 404
            }
            return jsonify(response), 404
        else:
            # Handle GUI requests with a template
            return render_template('error.html', error=f"Path not found: {error}"), 404

    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"500 error: {error}")
        # Check if the request is for the API
        if request.path.startswith('/api/'):  # The API base path

            response = {
                "error": "Server Error",
                "message": "Internal server error",
                "status": 500
            }
            return jsonify(response), 500
        else:
            # Handle GUI requests with a template
            return render_template('error.html', error=f"Internal server error: {error}"), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        # Check if the request is for the API
        if request.path.startswith('/api/'):  # The API base path

            response = {
                "error": "Server Error",
                "message": "Internal server error",
                "status": 500
            }
            return jsonify(response), 500
        else:
            # Handle GUI requests with a template
            return render_template('error.html', error=f"Internal server error: {error}"), 500