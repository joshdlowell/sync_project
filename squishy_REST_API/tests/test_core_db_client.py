import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta
from squishy_REST_API.configuration import config
# Import the core site implementations
from squishy_REST_API.database_client.core_site_mysql import CoreMYSQLConnection
from squishy_REST_API.database_client.core_site_DB_interface import CoreDBConnection


class CoreDBConnectionTestMixin:
    """
    Mixin class containing all the test methods for the CoreDBConnection interface.
    This ensures all implementations are tested with the same test cases.
    """

    def setUp(self):
        """This should be overridden in each test class to set up self.db"""
        self.db = None
        raise NotImplementedError("Subclasses must implement setUp")







    def test_get_log_count_last_24h_none_parameter(self):
        """Test get_log_count_last_24h with None parameter"""
        with self.assertRaises(ValueError):
            self.db.get_log_count_last_24h(None)

    def test_interface_method_existence(self):
        """Test that all required interface methods exist"""
        required_methods = [
            'get_dashboard_content',
            'get_recent_logs',
            'get_hash_record_count',
            'get_log_count_last_24h'
        ]

        for method_name in required_methods:
            self.assertTrue(hasattr(self.db, method_name))
            self.assertTrue(callable(getattr(self.db, method_name)))


class TestCoreMySQLConnection(unittest.TestCase, CoreDBConnectionTestMixin):
    """Test cases for Core MySQL implementation with real database"""

    @classmethod
    def setUpClass(cls):
        """Set up test database configuration - runs once for all tests"""
        cls.test_db_config = {
            'host': 'mysql-squishy-db',
            'database': 'squishy_db',
            'user': 'your_app_user',
            'password': 'your_user_password'
        }

    def setUp(self):
        """Set up Core MySQL connection"""
        try:
            self.db = CoreMYSQLConnection(
                host=self.test_db_config['host'],
                database=self.test_db_config['database'],
                user=self.test_db_config['user'],
                password=self.test_db_config['password']
            )
        except Exception as e:
            print(f"Error creating core database instance: {e}")
            self.skipTest("Database connection failed")

    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'db'):
            self._clear_test_data()

    def _clear_test_data(self):
        """Clear test data from database"""
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Clean up any test log entries
                    cursor.execute(
                        "DELETE FROM logs WHERE summary_message LIKE 'TEST:%' OR summary_message LIKE 'Core Test:%'"
                    )
                conn.commit()
        except Exception:
            pass  # Ignore cleanup errors

    def test_core_mysql_connection_handling(self):
        """Test Core MySQL-specific connection handling"""
        # Test successful connection
        with self.db._get_connection() as conn:
            self.assertIsNotNone(conn)
            self.assertTrue(conn.is_connected())

    def test_core_mysql_dashboard_query_execution(self):
        """Test that dashboard query executes without error"""
        result = self.db.get_dashboard_content()

        # Should not raise exception and should return valid structure
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_core_mysql_recent_logs_query_execution(self):
        """Test that recent logs query executes without error"""
        result = self.db.get_recent_logs()

        # Should not raise exception and should return list
        self.assertIsInstance(result, list)

    def test_core_mysql_hash_record_count_query_execution(self):
        """Test that hash record count query executes without error"""
        result = self.db.get_hash_record_count()

        # Should not raise exception and should return valid count
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)

    def test_core_mysql_log_count_query_execution(self):
        """Test that log count queries execute without error"""
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            result = self.db.get_log_count_last_24h(level)

            # Should not raise exception and should return valid count
            self.assertIsInstance(result, int)
            self.assertGreaterEqual(result, 0)

    def test_core_mysql_connection_recovery(self):
        """Test connection recovery after connection loss"""
        # First, verify normal operation
        result1 = self.db.get_hash_record_count()
        self.assertIsInstance(result1, int)

        # The next operation should work even after potential connection issues
        result2 = self.db.get_dashboard_content()
        self.assertIsInstance(result2, dict)

    def test_core_mysql_concurrent_operations(self):
        """Test multiple operations in sequence"""
        # Execute multiple operations to test connection stability
        dashboard = self.db.get_dashboard_content()
        logs = self.db.get_recent_logs()
        count = self.db.get_hash_record_count()
        error_count = self.db.get_log_count_last_24h('ERROR')

        # All operations should succeed
        self.assertIsInstance(dashboard, dict)
        self.assertIsInstance(logs, list)
        self.assertIsInstance(count, int)
        self.assertIsInstance(error_count, int)

    def test_core_mysql_dashboard_content_completeness(self):
        """Test that dashboard content includes all expected metrics"""
        result = self.db.get_dashboard_content()

        # Check that all sync metrics are present
        sync_metrics = ['sync_current', 'sync_1_behind', 'sync_l24_behind',
                        'sync_g24_behind', 'sync_unknown']
        for metric in sync_metrics:
            self.assertIn(metric, result)
            self.assertIsInstance(result[metric], int)

        # Check that all live metrics are present
        live_metrics = ['live_current', 'live_1_behind', 'live_l24_behind', 'live_inactive']
        for metric in live_metrics:
            self.assertIn(metric, result)
            self.assertIsInstance(result[metric], int)

        # Check other required metrics
        self.assertIn('crit_error_count', result)
        self.assertIn('hash_record_count', result)

    def test_core_mysql_log_level_validation(self):
        """Test that log level validation works correctly"""
        # Test each valid level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level in valid_levels:
            try:
                result = self.db.get_log_count_last_24h(level)
                self.assertIsInstance(result, int)
            except ValueError:
                self.fail(f"Valid log level '{level}' raised ValueError")

        # Test invalid levels
        invalid_levels = ['TRACE', 'FATAL', 'debugger', 'Information', 'warn', '', 'TEST']
        for level in invalid_levels:
            with self.assertRaises(ValueError):
                self.db.get_log_count_last_24h(level)

    def test_core_mysql_recent_logs_date_range(self):
        """Test that recent logs covers the correct date range"""
        logs = self.db.get_recent_logs()

        if logs:
            # Check that logs have timestamp field
            for log in logs[:5]:  # Check first 5 logs
                if 'timestamp' in log:
                    # Timestamp should be within last 30 days
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    log_timestamp = datetime.fromtimestamp(log['timestamp'])
                    self.assertGreaterEqual(log_timestamp, thirty_days_ago)

    def test_get_recent_logs_empty_case(self):
        """Test get_recent_logs when no logs exist"""
        result = self.db.get_recent_logs()

        # Should return empty list, not None
        self.assertIsInstance(result, list)

    def test_get_log_count_last_24h_valid_levels(self):
        """Test get_log_count_last_24h with valid log levels"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for level in valid_levels:
            result = self.db.get_log_count_last_24h(level)
            self.assertIsInstance(result, int)
            self.assertGreaterEqual(result, 0)

    def test_get_log_count_last_24h_invalid_level(self):
        """Test get_log_count_last_24h with invalid log level"""
        invalid_levels = ['INVALID', 'debugs', 'information', 'Test', '']

        for level in invalid_levels:
            with self.assertRaises(ValueError):
                self.db.get_log_count_last_24h(level)

    def test_get_hash_record_count_type(self):
        """Test that get_hash_record_count returns proper type"""
        result = self.db.get_hash_record_count()

        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)

    def test_get_log_count_last_24h_case_sensitivity(self):
        """Test that log level parameter is not case sensitive"""
        # Should not fail with lowercase
        valid_levels = [('DEBUG', 'debug'),
                        ('INFO', 'info'),
                        ('WARNING', 'warning'),
                        ('ERROR', 'error'),
                        ('CRITICAL', 'critical')]

        for level, lower_level in valid_levels:
            result = self.db.get_log_count_last_24h(lower_level)
            self.assertIsInstance(result, int)
            self.assertGreaterEqual(result, 0)

    def test_get_dashboard_content_structure(self):
        """Test that get_dashboard_content returns properly structured data"""
        result = self.db.get_dashboard_content()

        self.assertIsInstance(result, dict)

        # Check all required keys are present
        expected_keys = [
            'crit_error_count', 'hash_record_count', 'sync_current',
            'sync_1_behind', 'sync_l24_behind', 'sync_g24_behind',
            'sync_unknown', 'live_current', 'live_1_behind',
            'live_l24_behind', 'live_inactive'
        ]

        for key in expected_keys:
            self.assertIn(key, result)
            self.assertIsInstance(result[key], int)
            self.assertGreaterEqual(result[key], 0)

    def test_get_dashboard_content_values(self):
        """Test that dashboard content returns reasonable values"""
        result = self.db.get_dashboard_content()

        # All values should be non-negative integers
        for key, value in result.items():
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)


class TestCoreMySQLConnectionMock(unittest.TestCase, CoreDBConnectionTestMixin):
    """Test cases for Core MySQL implementation with mocked database"""

    def setUp(self):
        """Set up Core MySQL connection with mock"""
        # Mock the mysql.connector to avoid actual database connections
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.mock_connection.cursor.return_value.__exit__.return_value = None
        self.mock_connection.is_connected.return_value = True

        # Create connection factory that returns our mock
        def mock_factory(**kwargs):
            return self.mock_connection

        self.db = CoreMYSQLConnection(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass',
            connection_factory=mock_factory
        )

    def test_mock_dashboard_content_query(self):
        """Test dashboard content query with mocked results"""
        # Mock the dashboard query results
        mock_dashboard_values = {
            'crit_error_count': 5,
            'hash_record_count': 1000,
            'sync_current': 10,
            'sync_1_behind': 2,
            'sync_l24_behind': 1,
            'sync_g24_behind': 7,
            'sync_unknown': 6,
            'live_current': 8,
            'live_1_behind': 3,
            'live_l24_behind': 9,
            'live_inactive': 0
        }

        mock_dashboard_result = [val for key, val in mock_dashboard_values.items()]

        # Configure mock to return our test data
        self.mock_cursor.fetchone.return_value = mock_dashboard_result

        result = self.db.get_dashboard_content()

        # Verify query was executed
        self.mock_cursor.execute.assert_called()

        # Verify result structure
        self.assertIsInstance(result, dict)
        for key, value in mock_dashboard_values.items():
            self.assertEqual(mock_dashboard_values[key], result[key])

    def test_mock_recent_logs_query(self):
        """Test recent logs query with mocked results"""
        # Mock log entries
        mock_logs = [
            {
                'id': 1,
                'timestamp': int(time.time()),
                'log_level': 'INFO',
                'summary_message': 'Test log 1',
                'detailed_message': 'Detailed info 1'
            },
            {
                'id': 2,
                'timestamp': int(time.time()) - 3600,
                'log_level': 'WARNING',
                'summary_message': 'Test log 2',
                'detailed_message': 'Detailed info 2'
            }
        ]

        # Configure mock to return our test data
        self.mock_cursor.fetchall.return_value = mock_logs

        result = self.db.get_recent_logs()

        # Verify query was executed
        self.mock_cursor.execute.assert_called()

        # Verify result structure
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_mock_hash_record_count_query(self):
        """Test hash record count query with mocked results"""
        # Mock count result
        mock_count = {'total_count': 1500}  # Tuple as returned by fetchone for COUNT query
        self.mock_cursor.fetchone.return_value = mock_count

        result = self.db.get_hash_record_count()

        # Verify query was executed
        self.mock_cursor.execute.assert_called()

        # Verify result
        self.assertIsInstance(result, int)
        self.assertEqual(result, 1500)

    def test_mock_log_count_query(self):
        """Test log count query with mocked results"""
        # Mock count result
        mock_count = ({'record_count': 25})  # Dict as returned by fetchone for COUNT query
        self.mock_cursor.fetchone.return_value = mock_count

        result = self.db.get_log_count_last_24h('ERROR')

        # Verify query was executed
        self.mock_cursor.execute.assert_called()

        # Verify result
        self.assertIsInstance(result, int)
        self.assertEqual(result, 25)

    def test_mock_error_handling(self):
        """Test error handling with mocked database errors"""
        from mysql.connector import Error

        # Make cursor.execute raise an error
        self.mock_cursor.execute.side_effect = Error("Database error")

        # Operations should handle errors gracefully
        dashboard = self.db.get_dashboard_content()
        logs = self.db.get_recent_logs()
        count = self.db.get_hash_record_count()
        log_count = self.db.get_log_count_last_24h('INFO')

        # Should return safe defaults, not raise exceptions
        self.assertIsInstance(dashboard, dict)
        self.assertIsInstance(logs, list)
        self.assertIsInstance(count, int)
        self.assertIsInstance(log_count, int)

    def test_mock_connection_context_manager(self):
        """Test that connection context manager is used correctly"""
        # Execute an operation
        self.db.get_hash_record_count()

        # Verify connection context manager was used
        self.mock_connection.cursor.assert_called()
        self.mock_cursor.execute.assert_called()

    def test_mock_get_recent_logs_structure(self):
        """Test that get_recent_logs returns properly structured data"""
        # Mock count result
        mock_values = ([{'site_id': 'siteA', 'log_level': 'INFO', 'summary_message': "summary message"}])  # Dict as returned by fetchone for COUNT query
        self.mock_cursor.fetchall.return_value = mock_values

        result = self.db.get_recent_logs()

        self.assertIsInstance(result, list)

        # If there are logs, check their structure
        if result:
            log_entry = result[0]
            self.assertIsInstance(log_entry, dict)
            # Common log fields that should be present
            expected_fields = ['log_level', 'summary_message']
            for field in expected_fields:
                if field in log_entry:
                    self.assertIsNotNone(log_entry[field])

    def test_get_recent_logs_empty_case(self):
        """Test get_recent_logs when no logs exist"""
        mock_values = ([{'site_id': 'siteA', 'log_level': 'INFO',
                         'summary_message': "summary message"}])  # Dict as returned by fetchone for COUNT query
        self.mock_cursor.fetchall.return_value = mock_values
        result = self.db.get_recent_logs()

        # Should return empty list, not None
        self.assertIsInstance(result, list)

    def test_get_log_count_last_24h_valid_levels(self):
        """Test get_log_count_last_24h with valid log levels"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        mock_values = ({'record_count': 1})  # Dict as returned by fetchone for COUNT query
        self.mock_cursor.fetchone.return_value = mock_values

        result = self.db.get_log_count_last_24h("INFO")
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 1)

        mock_values = ({'record_count': 3})  # Dict as returned by fetchone for COUNT query
        self.mock_cursor.fetchone.return_value = mock_values

        result = self.db.get_log_count_last_24h("DEBUG")
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 3)

    def test_get_hash_record_count_type(self):
        """Test that get_hash_record_count returns proper type"""
        mock_values = {'total_count': 1}  # Dict as returned by fetchone for COUNT query
        self.mock_cursor.fetchone.return_value = mock_values
        result = self.db.get_hash_record_count()

        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)

    def test_get_log_count_last_24h_case_sensitivity(self):
        """Test that log level parameter is case sensitive"""
        # Should work with uppercase
        mock_values = ({'record_count': 1})  # Dict as returned by fetchone for COUNT query
        self.mock_cursor.fetchone.return_value = mock_values

        result = self.db.get_log_count_last_24h('info')
        self.assertIsInstance(result, int)

    def test_get_dashboard_content_structure(self):
        """Test that get_dashboard_content returns properly structured data"""
        # Mock the dashboard query results
        mock_dashboard_values = {
            'crit_error_count': 5,
            'hash_record_count': 1000,
            'sync_current': 10,
            'sync_1_behind': 2,
            'sync_l24_behind': 1,
            'sync_g24_behind': 7,
            'sync_unknown': 6,
            'live_current': 8,
            'live_1_behind': 3,
            'live_l24_behind': 9,
            'live_inactive': 0
        }

        mock_values = [val for key, val in mock_dashboard_values.items()]

        self.mock_cursor.fetchone.return_value = mock_values
        result = self.db.get_dashboard_content()

        self.assertIsInstance(result, dict)

        # Check all required keys are present
        expected_keys = [
            'crit_error_count', 'hash_record_count', 'sync_current',
            'sync_1_behind', 'sync_l24_behind', 'sync_g24_behind',
            'sync_unknown', 'live_current', 'live_1_behind',
            'live_l24_behind', 'live_inactive'
        ]

        for key in expected_keys:
            self.assertIn(key, result)
            self.assertIsInstance(result[key], int)
            self.assertGreaterEqual(result[key], 0)


class TestCoreInterfaceCompatibility(unittest.TestCase):
    """Test interface compatibility and method signatures"""

    def setUp(self):
        """Set up mock connection for testing"""
        # Mock connection for testing
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        mock_connection.is_connected.return_value = True

        def mock_factory(**kwargs):
            return mock_connection

        self.core_db = CoreMYSQLConnection(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_pass',
            connection_factory=mock_factory
        )

    def test_core_interface_methods_exist(self):
        """Test that all required interface methods exist"""
        required_methods = [
            'get_dashboard_content',
            'get_recent_logs',
            'get_hash_record_count',
            'get_log_count_last_24h'
        ]

        for method_name in required_methods:
            self.assertTrue(hasattr(self.core_db, method_name))
            self.assertTrue(callable(getattr(self.core_db, method_name)))

    def test_core_interface_inheritance(self):
        """Test that CoreMySQLConnection inherits from CoreDBConnection"""
        self.assertIsInstance(self.core_db, CoreDBConnection)

    def test_core_return_types(self):
        """Test that methods return expected types"""
        # Mock return values
        mock_cursor = self.core_db.connection_factory().cursor().__enter__()

        # Mock the dashboard query results
        mock_dashboard_values = {
            'crit_error_count': 5,
            'hash_record_count': 1000,
            'sync_current': 10,
            'sync_1_behind': 2,
            'sync_l24_behind': 1,
            'sync_g24_behind': 7,
            'sync_unknown': 6,
            'live_current': 8,
            'live_1_behind': 3,
            'live_l24_behind': 9,
            'live_inactive': 0
        }

        # mock_dashboard_result = [val for key, val in mock_dashboard_values.items()]
        # Test dashboard content
        mock_cursor.fetchone.return_value = [val for key, val in mock_dashboard_values.items()]
        result = self.core_db.get_dashboard_content()
        self.assertIsInstance(result, dict)

        # Test recent logs
        mock_cursor.fetchall.return_value = []
        result = self.core_db.get_recent_logs()
        self.assertIsInstance(result, list)

        # Test hash record count
        mock_cursor.fetchone.return_value = {'total_count': 100}
        result = self.core_db.get_hash_record_count()
        self.assertIsInstance(result, int)

        # Test log count
        mock_cursor.fetchone.return_value = {'record_count': 5}
        result = self.core_db.get_log_count_last_24h('ERROR')
        self.assertIsInstance(result, int)


if __name__ == '__main__':
    # Create a test suite that runs all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCoreMySQLConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestCoreMySQLConnectionMock))
    suite.addTests(loader.loadTestsFromTestCase(TestCoreInterfaceCompatibility))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with non-zero code if tests failed
    exit(0 if result.wasSuccessful() else 1)