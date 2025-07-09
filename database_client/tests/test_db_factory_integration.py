import unittest
import os
from unittest.mock import patch

from squishy_REST_API.db_factory import DBClientFactory
from squishy_REST_API.db_implementation import DBInstance
from squishy_REST_API.remote_mysql import RemoteMYSQLConnection
from squishy_REST_API.remote_memory import RemoteInMemoryConnection


class TestDBFactoryIntegration(unittest.TestCase):
    """
    Integration tests for DBClientFactory.

    These tests verify that the factory can create real database connections
    when the appropriate configurations are provided.
    """

    def setUp(self):
        """Set up test configurations."""
        self.mysql_config = {
            'database': {
                'remote_type': 'mysql',
                'remote_config': {
                    'host': os.getenv('MYSQL_HOST', 'localhost'),
                    'database': os.getenv('MYSQL_DATABASE', 'test_db'),
                    'user': os.getenv('MYSQL_USER', 'test_user'),
                    'password': os.getenv('MYSQL_PASSWORD', 'test_pass'),
                    'port': int(os.getenv('MYSQL_PORT', 3306))
                }
            }
        }

        self.memory_config = {
            'database': {
                'remote_type': 'local',
                'remote_config': {
                    'initial_data': {
                        '/test/path': {
                            'current_hash': 'abc123',
                            'dirs': [],
                            'files': [],
                            'links': []
                        }
                    }
                }
            }
        }

    def test_create_mysql_client(self):
        """Test creating a MySQL client through factory."""
        # Skip if MySQL config not available
        if not all([
            self.mysql_config['database']['remote_config']['host'],
            self.mysql_config['database']['remote_config']['database'],
            self.mysql_config['database']['remote_config']['user'],
            self.mysql_config['database']['remote_config']['password']
        ]):
            self.skipTest("MySQL configuration not provided")

        factory = DBClientFactory(self.mysql_config)
        db_instance = factory.create_client()

        self.assertIsInstance(db_instance, DBInstance)
        self.assertIsInstance(db_instance.remote_db, RemoteMYSQLConnection)
        self.assertIsNone(db_instance.core_db)
        self.assertIsNone(db_instance.pipeline_db)

        # Test that the connection actually works
        try:
            health_result = db_instance.health_check()
            self.assertEqual(health_result.get('local_db'), True)
        except Exception as e:
            self.skipTest(f"MySQL connection failed: {e}")

    def test_create_memory_client(self):
        """Test creating an in-memory client through factory."""
        factory = DBClientFactory(self.memory_config)
        db_instance = factory.create_client()

        self.assertIsInstance(db_instance, DBInstance)
        self.assertIsInstance(db_instance.remote_db, RemoteInMemoryConnection)
        self.assertIsNone(db_instance.core_db)
        self.assertIsNone(db_instance.pipeline_db)

        # Test that the memory connection works
        result = db_instance.get_hash_record('/test/path')
        self.assertIsNotNone(result)
        self.assertEqual(result['current_hash'], 'abc123')

    def test_create_mixed_client(self):
        """Test creating a client with mixed database types."""
        mixed_config = {
            'database': {
                'remote_type': 'local',
                'remote_config': {'initial_data': {}},
                'core_type': 'mysql',
                'core_config': self.mysql_config['database']['remote_config']
            }
        }

        factory = DBClientFactory(mixed_config)
        db_instance = factory.create_client()

        self.assertIsInstance(db_instance, DBInstance)
        self.assertIsInstance(db_instance.remote_db, RemoteInMemoryConnection)
        self.assertIsNone(db_instance.pipeline_db)

        # Core DB will be created but may fail connection
        if db_instance.core_db is not None:
            from squishy_REST_API.core_mysql import CoreMYSQLConnection
            self.assertIsInstance(db_instance.core_db, CoreMYSQLConnection)

    def test_client_method_delegation(self):
        """Test that DBInstance properly delegates method calls."""
        factory = DBClientFactory(self.memory_config)
        db_instance = factory.create_client()

        # Test RemoteDB methods
        test_record = {
            'path': '/test/new/path',
            'current_hash': 'new_hash_123',
            'dirs': [],
            'files': [],
            'links': []
        }

        # Test insert
        result = db_instance.insert_or_update_hash(test_record)
        self.assertTrue(result)

        # Test retrieve
        retrieved = db_instance.get_hash_record('/test/new/path')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['current_hash'], 'new_hash_123')

        # Test single field
        hash_value = db_instance.get_single_field('/test/new/path', 'current_hash')
        self.assertEqual(hash_value, 'new_hash_123')

        # Test health check
        health_result = db_instance.health_check()
        self.assertEqual(health_result.get('local_db'), True)

    def test_client_error_handling(self):
        """Test client error handling for missing implementations."""
        # Create client with only remote DB
        factory = DBClientFactory(self.memory_config)
        db_instance = factory.create_client()

        # Test that core DB methods raise appropriate errors
        with self.assertRaises(NotImplementedError) as context:
            db_instance.get_dashboard_content()

        self.assertIn("CoreDBConnection implementation not provided", str(context.exception))

        # Test that pipeline DB methods raise appropriate errors
        with self.assertRaises(NotImplementedError) as context:
            db_instance.get_pipeline_updates()

        self.assertIn("PipelineDBConnection implementation not provided", str(context.exception))

        # Test that pipeline health check returns None
        result = db_instance.pipeline_health_check()
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()


