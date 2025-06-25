# Storage Service (DBConnection) Interface Documentation

A Python abstract base class for database operations supporting hash table management and logging functionality.

## Table of Contents

- [Overview](#overview)
- [Available Implementations](#available-implementations)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Implementation Guide](#implementation-guide)
- [Best Practices](#best-practices)

## Overview

The `DBConnection` interface provides a standardized way to interact with different database backends for storing and retrieving file hash information and system logs. This abstraction allows you to switch between different storage implementations without changing your application code.

## Available Implementations

### Current Implementations

- **`local_memory.py`**: In-memory implementation using Python data structures (non-persistent)
- **`local_mysql.py`**: MySQL database implementation (persistent storage)

### Choosing an Implementation

#### Use `local_memory.py` for:
- Testing and development
- Temporary storage needs
- When persistence is not required
- Quick prototyping
- Unit testing scenarios

#### Use `local_mysql.py` for:
- Production environments
- When data persistence is required
- Multi-process or distributed systems
- Long-term data storage
- High-concurrency applications

## Installation

```python
# For memory implementation
from squishy_REST_API.storage_service.local_memory import LocalMemoryConnection

# For MySQL implementation  
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection

# Import the base interface for type hints
from squishy_REST_API.storage_service.db_connection import DBConnection
```

## Quick Start

```python
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection

# Initialize your chosen implementation
db = MYSQLConnection()

# Check database health
if not db.life_check():
    raise Exception("Database connection failed")

# Insert or update a hash record
record = {
    'path': '/home/user/document.txt',
    'current_hash': 'abc123def456',
    'timestamp': 1640995200
}
result = db.insert_or_update_hash(record)

# Retrieve a hash record
hash_record = db.get_hash_record('/home/user/document.txt')

# Get just the hash value
hash_value = db.get_single_hash_record('/home/user/document.txt')
```

## API Reference

### Classes

#### DBConnection

Abstract base class defining the storage service interface.

```python
from abc import ABC, abstractmethod

class DBConnection(ABC):
    """Abstract base class for database connections."""
```

### Hash Management Methods

#### insert_or_update_hash()

Insert a new hash record or update an existing one.

```python
def insert_or_update_hash(self, record: dict[str, Any]) -> Optional[Dict[str, list]]
```

**Parameters:**
- `record` (dict): Dictionary containing hash table column-value pairs

**Returns:**
- `Optional[Dict[str, list]]`: Dictionary with modified, created, and deleted paths, or `None` on error

**Raises:**
- `ValueError`: If required parameters are missing

**Example:**
```python
record = {
    'path': '/path/to/file',
    'current_hash': 'sha256hash',
    'timestamp': 1640995200,
    'target_hash': 'expected_hash'
}
result = db.insert_or_update_hash(record)
```

#### get_hash_record()

Retrieve a complete hash record by path.

```python
def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `path` (str): File or directory path

**Returns:**
- `Optional[Dict[str, Any]]`: Complete record data or `None` if not found

**Example:**
```python
record = db.get_hash_record('/home/user/file.txt')
if record:
    print(f"Hash: {record['current_hash']}")
    print(f"Timestamp: {record['timestamp']}")
```

#### get_single_hash_record()

Get only the current hash value for a specific path.

```python
def get_single_hash_record(self, path: str) -> Optional[str]
```

**Parameters:**
- `path` (str): File or directory path

**Returns:**
- `Optional[str]`: Hash value or `None` if not found

**Example:**
```python
hash_value = db.get_single_hash_record('/path/to/file')
if hash_value:
    print(f"Current hash: {hash_value}")
```

#### get_single_timestamp()

Get only the timestamp for a specific path.

```python
def get_single_timestamp(self, path: str) -> Optional[int]
```

**Parameters:**
- `path` (str): File or directory path

**Returns:**
- `Optional[int]`: Timestamp value or `None` if not found

**Example:**
```python
timestamp = db.get_single_timestamp('/path/to/file')
if timestamp:
    print(f"Last updated: {timestamp}")
```

### Priority and Update Methods

#### get_oldest_updates()

Retrieve directories that need updates based on age.

```python
def get_oldest_updates(self, root_path: str, percent: int = 10) -> List[str]
```

**Parameters:**
- `root_path` (str): Root directory to search from
- `percent` (int, optional): Percentage of directories to return (default: 10%)

**Returns:**
- `List[str]`: List of directory paths needing updates

**Example:**
```python
# Get 20% of oldest directories under /home
old_dirs = db.get_oldest_updates('/home', percent=20)
for directory in old_dirs:
    print(f"Update needed: {directory}")
```

#### get_priority_updates()

Get directories where target hash doesn't match current hash.

```python
def get_priority_updates(self) -> List[str]
```

**Returns:**
- `List[str]`: List of directory paths requiring immediate attention

**Example:**
```python
priority_dirs = db.get_priority_updates()
for directory in priority_dirs:
    print(f"Priority update needed: {directory}")
```

### Logging Methods

#### put_log()

Insert a log entry into the database.

```python
def put_log(self, args_dict: dict) -> int | None
```

**Parameters:**
- `args_dict` (dict): Log entry data

**Returns:**
- `int | None`: Log ID if successful, `None` on error

**Example:**
```python
log_entry = {
    'level': 'INFO',
    'message': 'Hash update completed',
    'timestamp': 1640995200,
    'component': 'hash_checker'
}
log_id = db.put_log(log_entry)
```

#### get_logs()

Retrieve log entries with pagination and ordering.

```python
def get_logs(self, limit: Optional[int] = None, offset: int = 0, 
            order_by: str = "timestamp", order_direction: str = "DESC") -> List[Dict[str, Any]]
```

**Parameters:**
- `limit` (Optional[int]): Maximum records to return (default: None for all)
- `offset` (int): Records to skip for pagination (default: 0)
- `order_by` (str): Column to order by (default: "timestamp")
- `order_direction` (str): Sort direction "ASC" or "DESC" (default: "DESC")

**Returns:**
- `List[Dict[str, Any]]`: List of log entries

**Raises:**
- `ValueError`: If invalid parameters provided

**Example:**
```python
# Get latest 50 log entries
recent_logs = db.get_logs(limit=50)

# Get logs with pagination
page_2_logs = db.get_logs(limit=25, offset=25)

# Get oldest logs first
old_logs = db.get_logs(order_direction="ASC")
```

#### delete_log_entry()

Remove a log entry from the database.

```python
def delete_log_entry(self, log_id: int) -> bool
```

**Parameters:**
- `log_id` (int): Log entry ID to delete

**Returns:**
- `bool`: `True` if deleted successfully, `False` otherwise

**Example:**
```python
success = db.delete_log_entry(12345)
if success:
    print("Log entry deleted")
```

### System Methods

#### life_check()

Check if the database is active and responsive.

```python
def life_check(self) -> bool
```

**Returns:**
- `bool`: `True` if database is responsive, `False` otherwise

**Example:**
```python
if db.life_check():
    print("Database is healthy")
else:
    print("Database connection issues detected")
```

## Usage Examples

### Basic Hash Management

```python
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection

# Initialize database connection
db = MYSQLConnection()

# Create a hash record
record = {
    'path': '/home/user/documents/report.pdf',
    'current_hash': 'd4f8c9a7b3e2f1a8c6d9e2b4f7a1c5e8',
    'timestamp': int(time.time()),
    'target_hash': 'd4f8c9a7b3e2f1a8c6d9e2b4f7a1c5e8'
}

# Insert the record
result = db.insert_or_update_hash(record)
if result:
    print(f"Record processed: {result}")
```

### Batch Operations

```python
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection
import time

db = MYSQLConnection()

# Process multiple files
files_to_process = [
    '/home/user/file1.txt',
    '/home/user/file2.txt',
    '/home/user/file3.txt'
]

for file_path in files_to_process:
    # Check if file already exists
    existing_hash = db.get_single_hash_record(file_path)
    
    if existing_hash:
        print(f"File {file_path} already tracked with hash: {existing_hash}")
    else:
        # Add new file
        record = {
            'path': file_path,
            'current_hash': f'hash_for_{file_path}',
            'timestamp': int(time.time())
        }
        db.insert_or_update_hash(record)
        print(f"Added tracking for: {file_path}")
```

### Priority Management

```python
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection

db = MYSQLConnection()

# Get directories needing immediate attention
priority_updates = db.get_priority_updates()
print(f"Found {len(priority_updates)} priority updates needed")

# Get oldest 15% of directories for routine updates
routine_updates = db.get_oldest_updates('/home/user', percent=15)
print(f"Found {len(routine_updates)} directories for routine updates")

# Process priority updates first
for path in priority_updates:
    print(f"Processing priority update for: {path}")
    # Your update logic here
```

### Logging Operations

```python
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection
import time

db = MYSQLConnection()

# Add log entries
log_entries = [
    {
        'level': 'INFO',
        'message': 'System startup completed',
        'timestamp': int(time.time()),
        'component': 'system'
    },
    {
        'level': 'WARNING',
        'message': 'High memory usage detected',
        'timestamp': int(time.time()),
        'component': 'monitor'
    }
]

for entry in log_entries:
    log_id = db.put_log(entry)
    print(f"Created log entry with ID: {log_id}")

# Retrieve and display recent logs
recent_logs = db.get_logs(limit=10)
for log in recent_logs:
    print(f"[{log['level']}] {log['message']} - {log['component']}")
```

### Switching Implementations

```python
from squishy_REST_API.storage_service.local_memory import LocalMemoryConnection
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection
from squishy_REST_API.storage_service.db_connection import DBConnection

def create_db_connection(use_persistent: bool = True) -> DBConnection:
    """Factory function to create appropriate database connection."""
    if use_persistent:
        return MYSQLConnection()
    else:
        return LocalMemoryConnection()

# Use in development
dev_db = create_db_connection(use_persistent=False)

# Use in production
prod_db = create_db_connection(use_persistent=True)

# Same interface for both
dev_db.life_check()
prod_db.life_check()
```

## Error Handling

### Graceful Error Handling

All methods handle errors gracefully by returning appropriate default values:

- Methods returning `Optional[T]` return `None` on error
- Methods returning `List[T]` return empty lists on error  
- Methods returning `bool` return `False` on error
- Methods returning `int | None` return `None` on error

### Exception Handling

For specific error conditions, some methods may raise `ValueError` for invalid parameters:

```python
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection

db = MYSQLConnection()

try:
    # This might raise ValueError for invalid parameters
    logs = db.get_logs(limit=-1)  # Invalid limit
except ValueError as e:
    print(f"Invalid parameter: {e}")

try:
    # This might raise ValueError for missing required fields
    result = db.insert_or_update_hash({})  # Empty record
except ValueError as e:
    print(f"Missing required fields: {e}")
```

### Connection Error Handling

```python
from squishy_REST_API.storage_service.local_mysql import MYSQLConnection

def safe_database_operation():
    db = MYSQLConnection()
    
    # Always check connection health first
    if not db.life_check():
        print("Database connection failed - using fallback behavior")
        return None
    
    # Proceed with operations
    record = db.get_hash_record('/some/path')
    return record

# Use with error handling
try:
    result = safe_database_operation()
    if result is None:
        print("Operation failed or returned no data")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Implementation Guide

### Creating Custom Implementations

To create a new storage backend, inherit from `DBConnection` and implement all abstract methods:

```python
from squishy_REST_API.storage_service.db_connection import DBConnection
from typing import Optional, Dict, List, Any

class CustomDBConnection(DBConnection):
    
    def __init__(self):
        # Initialize your custom storage backend
        pass
    
    def insert_or_update_hash(self, record: dict[str, Any]) -> Optional[Dict[str, list]]:
        # Implement hash insertion/update logic
        pass
    
    def get_hash_record(self, path: str) -> Optional[Dict[str, Any]]:
        # Implement hash record retrieval
        pass
    
    # Implement all other abstract methods...
    
    def life_check(self) -> bool:
        # Implement health check for your backend
        pass
```

### Required Methods

All implementations must provide:

- **Hash Management**: `insert_or_update_hash`, `get_hash_record`, `get_single_hash_record`, `get_single_timestamp`
- **Priority Management**: `get_oldest_updates`, `get_priority_updates`  
- **Logging**: `put_log`, `get_logs`, `delete_log_entry`
- **System Health**: `life_check`

## Best Practices

### Connection Management

1. **Check Health Early**: Always call `life_check()` after initialization
2. **Handle Failures Gracefully**: Design your application to handle database failures
3. **Use Appropriate Implementation**: Choose the right storage backend for your use case

### Performance Optimization

1. **Batch Operations**: Group multiple operations when possible
2. **Limit Query Results**: Use pagination parameters for large datasets
3. **Cache Frequently Accessed Data**: Consider caching hash values that are accessed repeatedly

### Error Handling

1. **Validate Inputs**: Check parameters before calling database methods
2. **Handle None Returns**: Always check for `None` returns from optional methods
3. **Log Errors**: Use the logging functionality to track database issues

### Security Considerations

1. **Sanitize Inputs**: Validate and sanitize all user inputs
2. **Use Parameterized Queries**: Implementations should use parameterized queries to prevent injection
3. **Limit Access**: Restrict database access to necessary operations only

## Contributing

When adding new implementations or extending the interface:

1. **Follow the Abstract Interface**: Implement all required methods
2. **Maintain Consistency**: Keep method signatures and return types consistent
3. **Add Tests**: Include comprehensive tests for new implementations
4. **Update Documentation**: Add examples and usage patterns for new features
5. **Handle Errors Gracefully**: Follow the established error handling patterns