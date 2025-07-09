import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from squishy_REST_API.db_factory import DBClientFactory
from squishy_REST_API.db_implementation import DBInstance
from squishy_REST_API.remote_memory import RemoteInMemoryConnection
from squishy_REST_API.remote_mysql import RemoteMYSQLConnection
from squishy_REST_API.core_mysql import CoreMYSQLConnection
from squishy_REST_API.pipeline_mssql import PipelineMSSQLConnection


class TestDBClientFactory(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_config = {
            'database': {
                'remote_type': 'mysql',
                'remote_config': {
                    'host': 'localhost',
                    'database': 'test_db',
                    'user': 'test_user',
                    'password': 'test_pass'
                },
                'core_type': 'mysql',
                'core_config': {
                    'host': 'core_host',
                    'database': 'core_db',
                    'user': 'core_user',
                    'password': 'core_pass'
                },
                'pipeline_type': 'mssql',
                'pipeline_config': {
                    'server': 'pipeline_server',
                    'database': 'pipeline_db',
                    'username': 'pipeline_user',
                    'password': 'pipeline_pass'
                }
            }
        }

    def test_init_with_config(self):
        """Test factory initialization with config."""
        factory = DBClientFactory(self.mock_config)
        self.assertEqual(factory.config, self.mock_config)

    def test_init_without_config(self):
        """Test factory initialization without config."""
        factory = DBClientFactory()
        self.assertEqual(factory.config, {})

    @patch('squishy_REST_API.db_factory.RemoteMYSQLConnection')
    @patch('squishy_REST_API.db_factory.CoreMYSQLConnection')
    @patch('squishy_REST_API.db_factory.PipelineMSSQLConnection')
    def test_create_client_with_all_types(self, mock_pipeline, mock_core, mock_remote):
        """Test creating client with all database types configured."""
        # Setup mocks
        mock_remote_instance = Mock()
        mock_core_instance = Mock()
        mock_pipeline_instance = Mock()

        mock_remote.return_value = mock_remote_instance
        mock_core.return_value = mock_core_instance
        mock_pipeline.return_value = mock_pipeline_instance

        factory = DBClientFactory(self.mock_config)
        db_instance = factory.create_client()

        # Verify instances were created with correct configs
        mock_remote.assert_called_once_with(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass'
        )
        mock_core.assert_called_once_with(
            host='core_host',
            database='core_db',
            user='core_user',
            password='core_pass'
        )
        mock_pipeline.assert_called_once_with(
            server='pipeline_server',
            database='pipeline_db',
            username='pipeline_user',
            password='pipeline_pass'
        )

        # Verify DBInstance was created correctly
        self.assertIsInstance(db_instance, DBInstance)
        self.assertEqual(db_instance.remote_db, mock_remote_instance)
        self.assertEqual(db_instance.core_db, mock_core_instance)
        self.assertEqual(db_instance.pipeline_db, mock_pipeline_instance)

    @patch('squishy_REST_API.db_factory.RemoteInMemoryConnection')
    def test_create_client_with_memory_db(self, mock_memory):
        """Test creating client with in-memory database."""
        config = {
            'database': {
                'remote_type': 'local',
                'remote_config': {'initial_data': {}}
            }
        }

        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        factory = DBClientFactory(config)
        db_instance = factory.create_client()

        mock_memory.assert_called_once_with(initial_data={})
        self.assertEqual(db_instance.remote_db, mock_memory_instance)
        self.assertIsNone(db_instance.core_db)
        self.assertIsNone(db_instance.pipeline_db)

    def test_create_client_with_empty_config(self):
        """Test creating client with empty config."""
        factory = DBClientFactory({})
        db_instance = factory.create_client()

        self.assertIsInstance(db_instance, DBInstance)
        self.assertIsNone(db_instance.remote_db)
        self.assertIsNone(db_instance.core_db)
        self.assertIsNone(db_instance.pipeline_db)

    def test_create_instance_with_none_class(self):
        """Test _create_instance with None class type."""
        factory = DBClientFactory()
        result = factory._create_instance(None, {'some': 'config'})
        self.assertIsNone(result)

    def test_create_instance_with_none_config(self):
        """Test _create_instance with None config."""
        factory = DBClientFactory()
        mock_class = Mock()
        mock_instance = Mock()
        mock_class.return_value = mock_instance

        result = factory._create_instance(mock_class, None)

        mock_class.assert_called_once_with()
        self.assertEqual(result, mock_instance)


if __name__ == '__main__':
    unittest.main()
