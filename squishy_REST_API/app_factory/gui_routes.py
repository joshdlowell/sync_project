"""
Routes module for REST API package.

This module defines the API routes and registers them with the Flask application.
"""
from flask import jsonify, request, Flask, render_template

from squishy_REST_API import logger


def register_gui_routes(app: Flask, db_instance):
    """
    Register web gui routes with the Flask application.

    Args:
        app: Flask application instance
        db_instance: The DBConnection instance to use for web requests
    """

    @app.route('/')
    def index():
        """Display the main dashboard with hashtable overview."""
        logger.debug("GET / - Dashboard request")
        try:
            # Get some summary data from your database
            # You'll need to implement these methods in your db_instance if they don't exist
            # total_records = db_instance.get_total_record_count() if hasattr(db_instance,
            #                                                                 'get_total_record_count') else 0
            # recent_updates = db_instance.get_recent_updates(limit=10) if hasattr(db_instance,
            #                                                                      'get_recent_updates') else []
            #
            # return render_template('dashboard.html',
            #                        total_records=total_records,
            #                        recent_updates=recent_updates)

            return render_template('dashboard.html',
                                   total_records=7,
                                   recent_updates=1)
        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            return render_template('error.html', error="Failed to load dashboard"), 500

    @app.route('/web/hashtable')
    def web_hashtable_list():
        """Display all hashtable records in HTML format."""
        logger.debug("GET /web/hashtable - HTML hashtable list request")
        try:
            # Get all records or implement pagination
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            search = request.args.get('search', '')

            # You'll need to implement these methods in your db_instance
            if search:
                records = db_instance.search_hash_records(search, page, per_page) if hasattr(db_instance,
                                                                                             'search_hash_records') else []
            else:
                records = db_instance.get_all_hash_records(page, per_page) if hasattr(db_instance,
                                                                                      'get_all_hash_records') else []

            total_count = db_instance.get_total_record_count() if hasattr(db_instance,
                                                                          'get_total_record_count') else len(records)

            return render_template('hashtable_list.html',
                                   records=records,
                                   page=page,
                                   per_page=per_page,
                                   total_count=total_count,
                                   search=search)
        except Exception as e:
            logger.error(f"Error rendering hashtable list: {e}")
            return render_template('error.html', error="Failed to load hashtable records"), 500

    @app.route('/web/hashtable/<path:file_path>')
    def web_hashtable_detail(file_path):
        """Display detailed view of a specific hashtable record."""
        logger.debug(f"GET /web/hashtable/{file_path} - HTML hashtable detail request")
        try:

            record = db_instance.get_hash_record(f"/{file_path}")
            logger.debug(record)
            if not record:
                logger.info(f"Path not found: {file_path}")
                return render_template('error.html', error=f"Path not found: {file_path}"), 405

            return render_template('hashtable_detail.html',
                                   record=record,
                                   file_path=file_path)
        except Exception as e:
            logger.error(f"Error rendering hashtable detail: {e}")
            return render_template('error.html', error="Failed to load record details"), 500

    register_error_handlers(app)

    logger.info("web-gui routes registered")
    # @app.route('/web/priority')
    # def web_priority_list():
    #     """Display priority updates in HTML format."""
    #     logger.debug("GET /web/priority - HTML priority list request")
    #     try:
    #         root_path = request.args.get('root_path', '/')
    #         percent = request.args.get('percent', 10, type=int)
    #
    #         priority_records = db_instance.get_oldest_updates(root_path, percent)
    #
    #         return render_template('priority_list.html',
    #                                priority_records=priority_records,
    #                                root_path=root_path,
    #                                percent=percent)
    #     except Exception as e:
    #         logger.error(f"Error rendering priority list: {e}")
    #         return render_template('error.html', error="Failed to load priority records"), 500

def register_error_handlers(app: Flask):
    """
    Register error handlers with the Flask application.

    Args:
        app: Flask application instance
    """
    @app.errorhandler(405)
    def not_found(error):
        logger.info(f"404 error: {error}")
        return render_template('error.html', error=f"Path not found: {error}"), 404

    @app.errorhandler(501)
    def server_error(error):
        logger.error(f"500 error: {error}")
        return jsonify({"message": "Internal server error"}), 500

    # @app.errorhandler(Exception)
    # def handle_exception(error):
    #     logger.error(f"Unhandled exception: {error}", exc_info=True)
    #     return jsonify({"message": "Internal server error"}), 500