import unittest
import os
from unittest.mock import patch
import mysql.connector
from mysql.connector import Error

from database_client.db_factory import DBClientFactory
from database_client.db_implementation import DBInstance
from database_client.remote_mysql import RemoteMYSQLConnection
from database_client.remote_memory import RemoteInMemoryConnection


class TestDBFactoryIntegration(unittest.TestCase):
    """
    Integration tests for DBClientFactory.

    These tests verify that the factory can create real database connections
    when the appropriate configurations are provided.
    """
    @classmethod
    def setUpClass(cls):
        """Set up test database connection."""
        cls.db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'database': os.getenv('MYSQL_DATABASE', 'squishy_db'),
            'user': os.getenv('MYSQL_USER', 'your_app_user'),
            'password': os.getenv('MYSQL_PASSWORD', 'your_user_password'),
            'port': int(os.getenv('MYSQL_PORT', 3306))
        }

        # Skip tests if database config is not provided
        if not all([cls.db_config['host'], cls.db_config['database'],
                    cls.db_config['user'], cls.db_config['password']]):
            raise unittest.SkipTest("MySQL database configuration not provided")

        # Test connection
        try:
            with mysql.connector.connect(**cls.db_config) as conn:
                pass
        except Error as e:
            raise unittest.SkipTest(f"Cannot connect to MySQL database: {e}")

        cls.db_conn = RemoteMYSQLConnection(**cls.db_config)
        cls._setup_test_tables()

    @classmethod
    def _setup_test_tables(cls):
        """Set up test tables."""
        try:
            with mysql.connector.connect(**cls.db_config) as conn:
                with conn.cursor() as cursor:
                    # Create hashtable if it doesn't exist
                    cursor.execute("""
                                   CREATE TABLE IF NOT EXISTS hashtable
                                   (
                                       path               VARCHAR(500) PRIMARY KEY,
                                       current_hash       VARCHAR(64),
                                       prev_hash          VARCHAR(64),
                                       current_dtg_latest BIGINT,
                                       prev_dtg_latest    BIGINT,
                                       current_dtg_first  BIGINT,
                                       dirs               JSON,
                                       files              JSON,
                                       links              JSON,
                                       target_hash        VARCHAR(64)
                                   )
                                   """)

                    # Create logs table if it doesn't exist
                    cursor.execute("""
                                   CREATE TABLE IF NOT EXISTS logs
                                   (
                                       log_id           INT AUTO_INCREMENT PRIMARY KEY,
                                       site_id          VARCHAR(100),
                                       log_level        VARCHAR(20),
                                       timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
                                       session_id       VARCHAR(100),
                                       summary_message  TEXT,
                                       detailed_message TEXT
                                   )
                                   """)
                    conn.commit()
        except Error as e:
            raise unittest.SkipTest(f"Cannot set up test tables: {e}")
    def setUp(self):
        """Set up test configurations."""
        self._cleanup_test_data()
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


        test_env_vars = {
            'LOCAL_DB_USER': 'test-user',
            'LOCAL_DB_PASSWORD': 'test-secret-key',
            'SITE_NAME': 'test1',
            'API_SECRET_KEY': 'test-secret-key',
            # Add other required env vars here
        }

        # Store original values to restore later
        self.original_env = {}
        for key, value in test_env_vars.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value


    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment variables
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Remove test data from database."""
        try:
            with mysql.connector.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM hashtable WHERE path LIKE '/test/%'")
                    cursor.execute("DELETE FROM logs WHERE summary_message LIKE 'Test%'")
                    conn.commit()
        except Error:
            pass  # Ignore cleanup errors

    # def test_create_mysql_client(self):
    #     """Test creating a MySQL client through factory."""
        # Skip if MySQL config not available
        # if not all([
        #     self.mysql_config['database']['remote_config']['host'],
        #     self.mysql_config['database']['remote_config']['database'],
        #     self.mysql_config['database']['remote_config']['user'],
        #     self.mysql_config['database']['remote_config']['password']
        # ]):
        #     self.skipTest("MySQL configuration not provided")
        #
        # factory = DBClientFactory(self.mysql_config)
        # db_instance = factory.create_client()
        #
        # self.assertIsInstance(db_instance, DBInstance)
        # self.assertIsInstance(db_instance.remote_db, RemoteMYSQLConnection)
        # self.assertIsNone(db_instance.core_db)
        # self.assertIsNone(db_instance.pipeline_db)
        #
        # # Test that the connection actually works
        # try:
        #     health_result = db_instance.health_check()
        #     self.assertEqual(health_result.get('local_db'), True)
        # except Exception as e:
        #     self.skipTest(f"MySQL connection failed: {e}")

    def test_create_memory_client(self):
        """Test creating an in-memory client through factory."""
        factory = DBClientFactory(self.memory_config)
        db_instance = factory.create_client()

        self.assertIsInstance(db_instance, DBInstance)
        self.assertIsInstance(db_instance.remote_db, RemoteInMemoryConnection)
        self.assertIsNone(db_instance.core_db)
        self.assertIsNone(db_instance.pipeline_db)

        db_instance.remote_db.hashtable = self.memory_config['database']['remote_config']['initial_data']

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
            from database_client.core_mysql import CoreMYSQLConnection
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


