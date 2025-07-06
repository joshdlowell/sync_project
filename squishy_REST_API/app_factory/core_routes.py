"""
Core Routes module for REST API package.

This module defines the API routes necessary for core site operations and registers them with the Flask application.
"""
from flask import jsonify, request, Flask, render_template
from datetime import datetime, timezone

from squishy_REST_API import logger, config


def register_core_routes(app: Flask, core_db_instance, db_instance):
    """
    Register web gui routes with the Flask application.

    Args:
        app: Flask application instance
        core_db_instance: The DBConnection instance to use for core site function web requests
        db_instance: The DBConnection instance to use for routine site web requests
    """

    @app.route('/api/orphans', methods=['GET'])
    def find_orphans():
        """Get all entries that aren't listed by a parent"""
        logger.debug(f"GET /api/orphans")

        # Get oldest updates from database
        orphaned_paths = db_instance.find_orphaned_entries()

        logger.info(f"Found {len(orphaned_paths)} orphaned entries")
        return jsonify({"message": "Success", "data": orphaned_paths}), 200


    @app.route('/api/untracked', methods=['GET'])
    def find_untracked():
        """Get a list of children claimed by a parent but not tracked in the database"""
        logger.debug(f"GET /api/untracked")

        # Get oldest updates from database
        untracked_paths = db_instance.find_untracked_children()

        logger.info(f"Found {len(untracked_paths)} untracked children")
        return jsonify({"message": "Success", "data": untracked_paths}), 200


    @app.route('/api/pipeline', methods=['GET'])
    def get_pipeline_updates():
        """Get a list of updates from the pipeline that haven't been processed yet."""
        logger.debug(f"GET /api/pipeline")

        # Get the pipeline updates
        pipeline_updates = pipeline_db_instance.get_pipeline_updates() # TODO need pipeline instance

        logger.info(f"Found {len(pipeline_updates)} unprocessed updates")
        return jsonify({"message": "Success", "data": pipeline_updates}), 200

    # Error handlers remain unchanged from api / gui routes imports