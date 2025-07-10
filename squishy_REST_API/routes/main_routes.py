from flask import Flask

from squishy_REST_API import logger
from . import api_routes, gui_routes, core_routes, error_handlers


def register_all_routes(app: Flask, db_instance, is_core_site=False):
    """Register all routes based on site type."""

    # Always register basic API routes
    api_routes.register_api_routes(app, db_instance)

    # Register core-specific routes if this is a core site
    if is_core_site:
        gui_routes.register_gui_routes(app, db_instance)
        core_routes.register_core_routes(app, db_instance)

    # Register error handlers
    error_handlers.register_error_handlers(app)
    logger.info(f"All remote {'and core' if is_core_site else ''} site routes registered.")