Here's the rewritten test class that uses a real MySQL database connection:

```python
import unittest
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

class TestMYSQLConnection(unittest.TestCase, DBConnectionTestMixin):
    """Test cases for MySQL implementation with real database"""

    @classmethod
    def setUpClass(cls):
        """Set up test database - runs once for all tests"""
        cls.test_db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'test_user'),
            'password': os.getenv('MYSQL_PASSWORD', 'test_pass'),
            'database': os.getenv('MYSQL_DATABASE', 'test_db')
        }
        
        # Create test database and tables
        cls._setup_test_database()

    @classmethod
    def _setup_test_database(cls):
        """Create test database and required tables"""
        try:
            # Connect without specifying database to create it
            connection = mysql.connector.connect(
                host=cls.test_db_config['host'],
                user=cls.test_db_config['user'],
                password=cls.test_db_config['password']
            )
            
            with connection.cursor() as cursor:
                # Create test database if it doesn't exist
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {cls.test_db_config['database']}")
                cursor.execute(f"USE {cls.test_db_config['database']}")
                
                # Create the required table structure
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS directory_hashes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        path VARCHAR(1000) NOT NULL UNIQUE,
                        current_hash VARCHAR(64) NOT NULL,
                        dirs JSON,
                        files JSON,
                        links JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
            connection.commit()
            connection.close()
            
        except Error as e:
            raise unittest.SkipTest(f"Could not setup test database: {e}")

    def setUp(self):
        """Set up MySQL connection for each test"""
        try:
            self.db = MYSQLConnection(**self.test_db_config)
            # Clear any existing test data
            self._clear_test_data()
        except Error as e:
            self.skipTest(f"Could not connect to test database: {e}")

    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'db'):
            self._clear_test_data()
            self.db.close()  # Assuming your MYSQLConnection has a close method

    def _clear_test_data(self):
        """Clear test data from database"""
        try:
            with self.db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM directory_hashes WHERE path LIKE '/test/%'")
                conn.commit()
        except Error:
            pass  # Ignore cleanup errors

    @classmethod
    def tearDownClass(cls):
        """Clean up test database - runs once after all tests"""
        try:
            connection = mysql.connector.connect(**cls.test_db_config)
            with connection.cursor() as cursor:
                cursor.execute(f"DROP DATABASE IF EXISTS {cls.test_db_config['database']}")
            connection.commit()
            connection.close()
        except Error:
            pass  # Ignore cleanup errors

    def test_mysql_specific_connection_handling(self):
        """Test MySQL-specific connection handling"""
        # Test successful connection
        with self.db._get_connection() as conn:
            self.assertIsNotNone(conn)
            self.assertTrue(conn.is_connected())

        # Connection should be properly managed by context manager
        # The connection might be pooled, so we can't test if it's closed directly

    def test_mysql_error_handling(self):
        """Test MySQL error handling"""
        # Create a connection with invalid credentials to test error handling
        invalid_config = self.test_db_config.copy()
        invalid_config['password'] = 'invalid_password'
        
        with self.assertRaises(Error):
            invalid_db = MYSQLConnection(**invalid_config)
            with invalid_db._get_connection() as conn:
                pass

    def test_mysql_insert_queries(self):
        """Test that MySQL queries work with real database"""
        record = {
            'path': '/test/path/mysql_test',
            'current_hash': 'abc123def456',
            'dirs': ['dir1', 'dir2'],
            'files': ['file1.txt', 'file2.py'],
            'links': ['link1']
        }

        # Insert the record
        result = self.db.insert_or_update_hash(record)

        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn('created', result)
        self.assertIn('modified', result)
        self.assertIn('deleted', result)

        # Verify the record was actually inserted
        with self.db._get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM directory_hashes WHERE path = %s", 
                    (record['path'],)
                )
                stored_record = cursor.fetchone()
                
                self.assertIsNotNone(stored_record)
                self.assertEqual(stored_record['path'], record['path'])
                self.assertEqual(stored_record['current_hash'], record['current_hash'])

    def test_mysql_update_queries(self):
        """Test updating existing records"""
        # First insert a record
        original_record = {
            'path': '/test/path/update_test',
            'current_hash': 'original_hash',
            'dirs': ['original_dir'],
            'files': ['original_file.txt'],
            'links': []
        }
        
        self.db.insert_or_update_hash(original_record)
        
        # Update the record
        updated_record = original_record.copy()
        updated_record['current_hash'] = 'updated_hash'
        updated_record['files'] = ['original_file.txt', 'new_file.txt']
        
        result = self.db.insert_or_update_hash(updated_record)
        
        # Verify update was successful
        self.assertGreater(result['modified'], 0)
        
        # Verify the record was actually updated
        with self.db._get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * FROM directory_hashes WHERE path = %s", 
                    (updated_record['path'],)
                )
                stored_record = cursor.fetchone()
                
                self.assertEqual(stored_record['current_hash'], 'updated_hash')

    def test_mysql_connection_recovery(self):
        """Test connection recovery after connection loss"""
        # This test verifies that the connection can be re-established
        # First, verify normal operation
        with self.db._get_connection() as conn:
            self.assertTrue(conn.is_connected())
        
        # Simulate connection loss by closing the connection pool
        # (This depends on your MYSQLConnection implementation)
        if hasattr(self.db, '_connection_pool'):
            self.db._connection_pool.close()
        
        # The next operation should re-establish connection
        record = {
            'path': '/test/path/recovery_test',
            'current_hash': 'recovery_hash',
            'dirs': [],
            'files': ['recovery_file.txt'],
            'links': []
        }
        
        # This should work even after connection loss
        result = self.db.insert_or_update_hash(record)
        self.assertIsInstance(result, dict)
```

Key changes made:

1. **Real Database Setup**: Uses `setUpClass` and `tearDownClass` to create and destroy a real test database
2. **Environment Variables**: Uses environment variables for database configuration to make tests portable
3. **Database Schema**: Creates the actual table structure needed for tests
4. **Real Queries**: Tests actually execute against the database and verify results
5. **Connection Testing**: Tests real connection handling and error scenarios
6. **Data Cleanup**: Properly cleans up test data between tests
7. **Skip on Failure**: Uses `skipTest` when database connection fails rather than failing the test

To use these tests, you'll need to:

1. Set up environment variables for your test database
2. Ensure your test database server is running
3. Make sure the test user has permissions to create/drop databases
4. Install the `mysql-connector-python` package

Example environment setup:
```bash
export MYSQL_HOST=localhost
export MYSQL_USER=test_user
export MYSQL_PASSWORD=test_password
export MYSQL_DATABASE=test_directory_hashes
```