"""
Database module for REST API package.

This module provides a factory function to create database instances
using configuration from the config module.
"""
from typing import Optional, Dict, Type

from database_client import logging_config
from .db_implementation import DBInstance
from .remote_memory import RemoteInMemoryConnection
from .remote_mssql_untested import RemoteMSSQLConnection
from .remote_mysql import RemoteMYSQLConnection
from .core_mysql import CoreMYSQLConnection
from .pipeline_mssql import PipelineMSSQLConnection

class DBClientFactory:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging_config.configure_logging()

    def create_client(self) -> DBInstance:
        """Create a database client instance"""
        db_config = self.config.get('database', {})

        # Database implementation mappings
        remote_types = {
            'mysql': RemoteMYSQLConnection,
            'mssql': RemoteMSSQLConnection,
            'local': RemoteInMemoryConnection,
        }

        core_types = {
            'mysql': CoreMYSQLConnection,
        }

        pipeline_types = {
            'mssql': PipelineMSSQLConnection,
        }

        # Create instances
        remote_db = self._create_instance(
            remote_types.get(db_config.get('remote_type')),
            db_config.get('remote_config')
        )
        if remote_db:
            self.logger.info(f'Created remote database instance: {db_config.get("remote_type")}')

        core_db = self._create_instance(
            core_types.get(db_config.get('core_type')),
            db_config.get('core_config')
        )
        if core_db:
            self.logger.info(f'Created core database instance: {db_config.get("core_type")}')

        pipeline_db = self._create_instance(
            pipeline_types.get(db_config.get('pipeline_type')),
            db_config.get('pipeline_config')
        )
        if pipeline_db:
            self.logger.info(f'Created pipeline database instance: {db_config.get("pipeline_type")}')


        return DBInstance(remote_db=remote_db, core_db=core_db, pipeline_db=pipeline_db)

    def _create_instance(self, class_type: Optional[Type], config: Optional[Dict]):
        """Helper to create an instance with optional config"""
        if not class_type:
            return None
        return class_type(**(config or {}))
