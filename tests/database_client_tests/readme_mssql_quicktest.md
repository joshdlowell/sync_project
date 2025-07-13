I'll create a test script that you can easily modify to test different methods of your `PipelineMSSQLConnection` class. Here's `mssql_checks.py`:

```python
#!/usr/bin/env python3
"""
Test script for PipelineMSSQLConnection class methods.
Modify the test methods and connection parameters as needed.
"""

import sys
import os
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import the class
# Adjust this path as needed based on your project structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your class - adjust the import path as needed
from your_module_name import PipelineMSSQLConnection
import logging_config

def print_separator(title: str):
    """Print a visual separator for test sections."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_results(method_name: str, results: Any):
    """Print results in a formatted way."""
    print(f"\n{method_name} Results:")
    print("-" * 40)
    
    if isinstance(results, list):
        if not results:
            print("No results returned (empty list)")
        else:
            print(f"Returned {len(results)} items:")
            for i, item in enumerate(results, 1):
                print(f"  {i}. {item}")
    elif isinstance(results, dict):
        if not results:
            print("No results returned (empty dict)")
        else:
            print("Returned dictionary:")
            for key, value in results.items():
                print(f"  {key}: {value}")
    elif results is None:
        print("No results returned (None)")
    else:
        print(f"Result: {results}")

def test_connection_basic(db_instance: PipelineMSSQLConnection):
    """Test basic connection functionality."""
    print_separator("BASIC CONNECTION TEST")
    
    try:
        # Test getting all unprocessed updates
        print("Testing get_pipeline_updates()...")
        updates = db_instance.get_pipeline_updates()
        print_results("get_pipeline_updates", updates)
        
        # Test getting official sites
        print("\nTesting get_official_sites()...")
        sites = db_instance.get_official_sites()
        print_results("get_official_sites", sites)
        
    except Exception as e:
        print(f"Error in basic connection test: {e}")

def test_specific_queries(db_instance: PipelineMSSQLConnection):
    """Test specific query methods."""
    print_separator("SPECIFIC QUERY TESTS")
    
    # Test get_update_by_path - MODIFY THESE PATHS FOR YOUR DATA
    test_paths = [
        "/baseline/test",
        "/updates/version1.0",
        "/nonexistent/path"
    ]
    
    for path in test_paths:
        try:
            print(f"\nTesting get_update_by_path('{path}')...")
            result = db_instance.get_update_by_path(path)
            print_results(f"get_update_by_path('{path}')", result)
        except Exception as e:
            print(f"Error testing path '{path}': {e}")
    
    # Test get_processed_updates with different limits
    limits_to_test = [None, 5, 10]
    
    for limit in limits_to_test:
        try:
            print(f"\nTesting get_processed_updates(limit={limit})...")
            results = db_instance.get_processed_updates(limit)
            print_results(f"get_processed_updates(limit={limit})", results)
        except Exception as e:
            print(f"Error testing limit {limit}: {e}")

def test_hash_updates(db_instance: PipelineMSSQLConnection):
    """Test hash update functionality."""
    print_separator("HASH UPDATE TESTS")
    
    # MODIFY THESE TEST CASES FOR YOUR DATA
    test_cases = [
        {
            "path": "/baseline/test",
            "hash": "abc123def456"
        },
        {
            "path": "/updates/test_update",
            "hash": "xyz789uvw012"
        }
    ]
    
    for case in test_cases:
        try:
            print(f"\nTesting put_pipeline_hash('{case['path']}', '{case['hash']}')...")
            success = db_instance.put_pipeline_hash(case['path'], case['hash'])
            print_results(f"put_pipeline_hash", f"Success: {success}")
        except Exception as e:
            print(f"Error updating hash for '{case['path']}': {e}")

def test_error_conditions(db_instance: PipelineMSSQLConnection):
    """Test error handling."""
    print_separator("ERROR CONDITION TESTS")
    
    # Test with invalid inputs
    error_tests = [
        ("get_update_by_path with empty string", lambda: db_instance.get_update_by_path("")),
        ("get_update_by_path with None", lambda: db_instance.get_update_by_path(None)),
        ("put_pipeline_hash with empty path", lambda: db_instance.put_pipeline_hash("", "somehash")),
        ("put_pipeline_hash with empty hash", lambda: db_instance.put_pipeline_hash("/some/path", "")),
        ("get_processed_updates with invalid limit", lambda: db_instance.get_processed_updates(-1)),
    ]
    
    for test_name, test_func in error_tests:
        try:
            print(f"\nTesting {test_name}...")
            result = test_func()
            print_results(test_name, result)
        except Exception as e:
            print(f"Expected error for {test_name}: {e}")

def main():
    """Main test function."""
    print_separator("MSSQL CONNECTION TESTS")
    
    # CONNECTION CONFIGURATION - MODIFY THESE FOR YOUR DATABASE
    db_config = {
        'server': 'your_server_name',
        'database': 'your_database_name',
        'username': 'your_username',
        'password': 'your_password',
        'driver': 'ODBC Driver 17 for SQL Server',  # Adjust if needed
        'port': 1433,
        'connection_timeout': 30,
        'command_timeout': 30
    }
    
    # Alternative: Use environment variables for security
    # db_config = {
    #     'server': os.getenv('DB_SERVER'),
    #     'database': os.getenv('DB_NAME'),
    #     'username': os.getenv('DB_USER'),
    #     'password': os.getenv('DB_PASSWORD'),
    #     'driver': 'ODBC Driver 17 for SQL Server',
    #     'port': 1433,
    #     'connection_timeout': 30,
    #     'command_timeout': 30
    # }
    
    try:
        # Create database instance
        print("Creating database connection instance...")
        db_instance = PipelineMSSQLConnection(**db_config)
        print("Database instance created successfully!")
        
        # Run tests - COMMENT OUT SECTIONS YOU DON'T WANT TO RUN
        test_connection_basic(db_instance)
        test_specific_queries(db_instance)
        # test_hash_updates(db_instance)  # Uncomment to test hash updates
        # test_error_conditions(db_instance)  # Uncomment to test error conditions
        
        print_separator("TESTS COMPLETED")
        
    except Exception as e:
        print(f"Failed to create database instance or run tests: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
```

## How to use this script:

1. **Modify the import**: Change `from your_module_name import PipelineMSSQLConnection` to match your actual module structure.

2. **Update database configuration**: Edit the `db_config` dictionary with your actual database connection details.

3. **Customize test data**: Modify the test paths, hash values, and other test data throughout the script to match your actual database content.

4. **Run specific tests**: Comment/uncomment the test function calls in `main()` to run only the tests you want.

5. **Add custom tests**: Add your own test functions following the same pattern.

## Example usage scenarios:

```python
# Test a specific method quickly
def quick_test(db_instance):
    result = db_instance.get_update_by_path('/your/specific/path')
    print(f"Result: {result}")

# Add this to main() and comment out other tests
# quick_test(db_instance)
```

The script provides:
- Clear visual separation between test sections
- Formatted output for easy reading
- Error handling for individual tests
- Easy modification points for your specific data
- Modular test functions you can run independently

Just modify the configuration and test data, save the file, and run `python mssql_checks.py` to test your database integration!