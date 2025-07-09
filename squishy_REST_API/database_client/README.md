# Database Client Package

A modular and extensible database client library for hash storage and logging operations. This package provides a factory-based approach to database connections with support for MySQL, MSSQL, and in-memory implementations across remote, core, and pipeline database tiers.

## Table of Contents

- [Package Overview](#package-overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
  - [DBClientFactory](#dbclientfactory)
  - [DBInstance](#dbinstance)
  - [RemoteDBConnection](#remotedbconnection)
  - [CoreDBConnection](#coredbconnection)
  - [PipelineDBConnection](#pipelinedbconnection)
- [Development](#development)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Data Structures](#data-structures)
- [Examples](#examples)
- [Project Status](#project-status)
- [Version and Change Log](#version)
- [Roadmap](#roadmap)
- [Support](#support)
- [Acknowledgments](#acknowledgments)

## Package Overview

The Database Client package provides a comprehensive solution for database operations in hash storage and monitoring systems. It offers a factory-based approach to creating database connections with support for multiple database types and deployment tiers.

Key features:
- **Multi-Tier Architecture**: Separate connections for remote, core, and pipeline databases
- **Multiple Database Support**: MySQL, MSSQL, and in-memory implementations
- **Factory Pattern**: Easy instantiation and configuration management
- **Abstract Interfaces**: Clean separation between interface and implementation
- **Comprehensive Operations**: Hash storage, logging, health checks, and data integrity
- **Type Safety**: Full type annotations for better development experience
- **Robust Error Handling**: Comprehensive error management and logging

## Quick Start

```python
from database_client import DBClientFactory

# Configure database connections
config = {
    'database': {
        'remote_type': 'mysql',
        'remote_config': {
            'host': 'localhost',
            'database': 'hash_db',
            'user': 'user',
            'password': 'password'
        },
        'core_type': 'mysql',
        'core_config': {
            'host': 'core.example.com',
            'database': 'core_db',
            'user': 'core_user',
            'password': 'core_password'
        }
    }
}

# Create database client
factory = DBClientFactory(config)
db = factory.create_client()

# Store hash information
hash_record = {
    'path': '/home/user/documents',
    'current_hash': 'abc123def456',
    'dirs': ['subfolder1', 'subfolder2'],
    'files': ['document1.txt', 'document2.pdf'],
    'links': ['shortcut1']
}

success = db.insert_or_update_hash(hash_record)
print(f"Hash record {'stored' if success else 'failed'}")

# Retrieve hash information
record = db.get_hash_record('/home/user/documents')
if record:
    print(f"Current hash: {record.get('current_hash')}")
    print(f"Last updated: {record.get('current_dtg_latest')}")
```

## Installation

```python
# Import the package
from database_client import DBClientFactory
from database_client.db_interfaces import RemoteDBConnection, CoreDBConnection, PipelineDBConnection
```

## Configuration

### Database Configuration Structure

```python
config = {
    'database': {
        # Remote database configuration
        'remote_type': 'mysql',  # 'mysql', 'mssql', 'local'
        'remote_config': {
            'host': 'localhost',
            'database': 'remote_db',
            'user': 'remote_user',
            'password': 'remote_password',
            'port': 3306
        },
        
        # Core database configuration
        'core_type': 'mysql',  # 'mysql'
        'core_config': {
            'host': 'core.example.com',
            'database': 'core_db',
            'user': 'core_user',
            'password': 'core_password',
            'port': 3306
        },
        
        # Pipeline database configuration
        'pipeline_type': 'mssql',  # 'mssql'
        'pipeline_config': {
            'server': 'pipeline.example.com',
            'database': 'pipeline_db',
            'username': 'pipeline_user',
            'password': 'pipeline_password'
        }
    }
}
```

### Supported Database Types

| Tier     | Type    | Implementation        | Description                    |
|----------|---------|----------------------|--------------------------------|
| Remote   | mysql   | RemoteMYSQLConnection | MySQL for remote operations    |
| Remote   | mssql   | RemoteMSSQLConnection | MSSQL for remote operations    |
| Remote   | local   | RemoteInMemoryConnection | In-memory for testing       |
| Core     | mysql   | CoreMYSQLConnection   | MySQL for core operations      |
| Pipeline | mssql   | PipelineMSSQLConnection | MSSQL for pipeline operations |

## API Reference

### DBClientFactory

Factory class for creating database client instances with proper configuration.

#### Constructor

```python
DBClientFactory(config: Optional[Dict] = None)
```

**Parameters:**
- `config` (Optional[Dict]): Configuration dictionary containing database settings

#### Methods

##### `create_client() -> DBInstance`

Creates a fully configured database client instance.

**Returns:**
- `DBInstance`: Configured database client with remote, core, and pipeline connections

**Example:**
```python
factory = DBClientFactory(config)
db_client = factory.create_client()
```

---

### DBInstance

Main database client that combines remote, core, and pipeline database connections.

#### Constructor

```python
DBInstance(
    remote_db: Optional[RemoteDBConnection] = None,
    core_db: Optional[CoreDBConnection] = None,
    pipeline_db: Optional[PipelineDBConnection] = None
)
```

**Parameters:**
- `remote_db` (Optional[RemoteDBConnection]): Remote database connection
- `core_db` (Optional[CoreDBConnection]): Core database connection
- `pipeline_db` (Optional[PipelineDBConnection]): Pipeline database connection

---

### RemoteDBConnection

Interface for remote database operations including hash storage and logging.

#### Methods

##### `get_hash_record(path: str) -> Optional[Dict[str, Any]]`

Retrieves a complete hash record for a specific path.

**Parameters:**
- `path` (str): Path to retrieve record for

**Returns:**
- `Optional[Dict[str, Any]]`: Hash record dictionary or None if not found

**Example:**
```python
record = db.get_hash_record('/home/user/documents')
if record:
    print(f"Hash: {record['current_hash']}")
    print(f"Files: {record['files']}")
```

##### `insert_or_update_hash(record: dict[str, Any]) -> bool`

Inserts a new hash record or updates an existing one.

**Parameters:**
- `record` (dict[str, Any]): Hash record with required fields

**Returns:**
- `bool`: True if successful, False otherwise

**Required Fields:**
- `path`: File/directory path
- `current_hash`: Current hash value

**Optional Fields:**
- `dirs`: List of subdirectories
- `files`: List of files
- `links`: List of symbolic links
- `target_hash`: Target hash value
- `session_id`: Session identifier for logging

**Example:**
```python
record = {
    'path': '/home/user/documents',
    'current_hash': 'abc123def456',
    'dirs': ['subfolder1', 'subfolder2'],
    'files': ['document1.txt', 'document2.pdf'],
    'target_hash': 'abc123def456',
    'session_id': 'scan_20240108_001'
}
success = db.insert_or_update_hash(record)
```

##### `get_single_field(path: str, field: str) -> str | int | None`

Retrieves a single field value for a specific path.

**Parameters:**
- `path` (str): Path to retrieve field for
- `field` (str): Field name ('current_hash', 'current_dtg_latest')

**Returns:**
- `str | int | None`: Field value or None if not found

**Example:**
```python
hash_value = db.get_single_field('/home/user/documents', 'current_hash')
timestamp = db.get_single_field('/home/user/documents', 'current_dtg_latest')
```

##### `get_priority_updates() -> List[str]`

Gets directories where target hash doesn't match current hash.

**Returns:**
- `List[str]`: List of directory paths needing updates

**Example:**
```python
priority_paths = db.get_priority_updates()
for path in priority_paths:
    print(f"Priority update needed: {path}")
```

##### `put_log(args_dict: dict) -> int | None`

Inserts a log entry into the database.

**Parameters:**
- `args_dict` (dict): Log entry data

**Required Fields:**
- `summary_message`: Brief log message

**Optional Fields:**
- `site_id`: Site identifier
- `log_level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `session_id`: Session identifier
- `detailed_message`: Detailed log information

**Returns:**
- `int | None`: Log ID if successful, None otherwise

**Example:**
```python
log_entry = {
    'summary_message': 'Hash update completed',
    'detailed_message': 'Updated 5 directories successfully',
    'log_level': 'INFO',
    'session_id': 'scan_20240108_001'
}
log_id = db.put_log(log_entry)
```

##### `get_logs(limit: Optional[int] = None, offset: int = 0, order_by: str = "timestamp", order_direction: str = "DESC", session_id_filter: Optional[str] = None, older_than_days: Optional[int] = None) -> List[Dict[str, Any]]`

Retrieves log entries with filtering and pagination.

**Parameters:**
- `limit` (Optional[int]): Maximum number of records
- `offset` (int): Number of records to skip
- `order_by` (str): Column to order by
- `order_direction` (str): Sort direction ('ASC' or 'DESC')
- `session_id_filter` (Optional[str]): Filter by session ID
- `older_than_days` (Optional[int]): Filter by age in days

**Returns:**
- `List[Dict[str, Any]]`: List of log entries

**Example:**
```python
# Get recent logs
recent_logs = db.get_logs(limit=10, order_by='timestamp', order_direction='DESC')

# Get logs for specific session
session_logs = db.get_logs(session_id_filter='scan_20240108_001')

# Get old logs for cleanup
old_logs = db.get_logs(older_than_days=30)
```

##### `delete_log_entries(log_ids: list[int]) -> tuple[list, list]`

Deletes multiple log entries by their IDs.

**Parameters:**
- `log_ids` (list[int]): List of log IDs to delete

**Returns:**
- `tuple[list, list]`: (deleted_count, failed_deletes)

**Example:**
```python
deleted_count, failed_deletes = db.delete_log_entries([1, 2, 3, 4, 5])
print(f"Deleted {deleted_count} entries, {len(failed_deletes)} failed")
```

##### `find_orphaned_entries() -> list[str]`

Finds database entries that aren't listed by their parent directories.

**Returns:**
- `list[str]`: List of orphaned entry paths

##### `find_untracked_children() -> list[Any]`

Finds children listed by parents but don't exist as database entries.

**Returns:**
- `list[Any]`: List of untracked child paths

##### `health_check() -> dict[str, bool]`

Verifies database connectivity and responsiveness.

**Returns:**
- `dict[str, bool]`: Health status with 'local_db' key

**Example:**
```python
health = db.health_check()
if health['local_db']:
    print("Database is healthy")
else:
    print("Database connection failed")
```

---

### CoreDBConnection

Interface for core database operations including dashboard metrics and centralized logging.

#### Methods

##### `get_dashboard_content() -> dict[str, Any]`

Retrieves comprehensive dashboard metrics for site monitoring.

**Returns:**
- `dict[str, Any]`: Dashboard metrics including:
  - `crit_error_count`: Critical errors in last 24 hours
  - `hash_record_count`: Total hash records
  - `sync_current`: Sites with current sync status
  - `sync_1_behind`: Sites one baseline behind
  - `sync_l24_behind`: Sites with hash from last 24 hours
  - `sync_g24_behind`: Sites with hash older than 24 hours
  - `sync_unknown`: Sites with unknown baseline
  - `live_current`: Sites active in last 35 minutes
  - `live_1_behind`: Sites active between 35m-24h ago
  - `live_l24_behind`: Sites active in last 24 hours
  - `live_inactive`: Sites inactive for over 24 hours

**Example:**
```python
dashboard = db.get_dashboard_content()
print(f"Critical errors: {dashboard['crit_error_count']}")
print(f"Hash records: {dashboard['hash_record_count']}")
print(f"Sites in sync: {dashboard['sync_current']}")
```

##### `get_recent_logs() -> list`

Retrieves log entries from the last 30 days.

**Returns:**
- `list`: List of recent log entries

##### `get_hash_record_count() -> int`

Gets the total count of hash records.

**Returns:**
- `int`: Total number of hash records

##### `get_log_count_last_24h(log_level: str) -> int`

Gets count of log entries for a specific level in the last 24 hours.

**Parameters:**
- `log_level` (str): Log level to count ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

**Returns:**
- `int`: Count of matching log records

**Example:**
```python
error_count = db.get_log_count_last_24h('ERROR')
critical_count = db.get_log_count_last_24h('CRITICAL')
print(f"Errors: {error_count}, Critical: {critical_count}")
```

---

### PipelineDBConnection

Interface for pipeline database operations including update processing and site management.

#### Methods

##### `get_pipeline_updates() -> List[Dict[str, Any]]`

Retrieves pending updates from the pipeline.

**Returns:**
- `List[Dict[str, Any]]`: List of pipeline updates

##### `put_pipeline_hash(update_path: str, hash_value: str) -> bool`

Stores a hash value for a pipeline update.

**Parameters:**
- `update_path` (str): Path for the update
- `hash_value` (str): Hash value to store

**Returns:**
- `bool`: True if successful, False otherwise

##### `get_official_sites() -> List[str]`

Retrieves list of official site identifiers.

**Returns:**
- `List[str]`: List of official site names

##### `put_pipeline_site_completion(site: str) -> bool`

Records completion of pipeline processing for a site.

**Parameters:**
- `site` (str): Site identifier

**Returns:**
- `bool`: True if successful, False otherwise

##### `pipeline_health_check() -> Dict[str, bool]`

Verifies pipeline database connectivity.

**Returns:**
- `Dict[str, bool]`: Health status dictionary

---

## Error Handling

The package provides comprehensive error handling:

### Database Errors

- **Connection Errors**: Network connectivity issues
- **Authentication Errors**: Invalid credentials
- **Query Errors**: SQL syntax or execution errors
- **Timeout Errors**: Query execution timeouts
- **Data Integrity Errors**: Constraint violations

### Exception Types

- `mysql.connector.Error`: MySQL-specific errors
- `ValueError`: Invalid parameter values
- `TypeError`: Type validation errors
- `ConnectionError`: Database connection failures

### Logging

All operations are logged with appropriate levels:

- **DEBUG**: Detailed operation information
- **INFO**: General status updates
- **WARNING**: Recoverable errors and retries
- **ERROR**: Validation errors and failed operations
- **CRITICAL**: Connection errors and system failures

---

## Data Structures

### Hash Record Structure

```python
{
    "path": "/home/user/documents",
    "current_hash": "abc123def456",
    "prev_hash": "def456abc123",
    "current_dtg_latest": 1704672000,
    "current_dtg_first": 1704672000,
    "prev_dtg_latest": 1704585600,
    "dirs": ["subfolder1", "subfolder2"],
    "files": ["document1.txt", "document2.pdf"],
    "links": ["shortcut1"],
    "target_hash": "abc123def456"
}
```

### Log Entry Structure

```python
{
    "log_id": 12345,
    "site_id": "site001",
    "log_level": "INFO",
    "timestamp": "2024-01-08 10:30:00",
    "session_id": "scan_20240108_001",
    "summary_message": "Hash update completed",
    "detailed_message": "Updated 5 directories successfully"
}
```

### Dashboard Metrics Structure

```python
{
    "crit_error_count": 2,
    "hash_record_count": 15432,
    "sync_current": 45,
    "sync_1_behind": 8,
    "sync_l24_behind": 3,
    "sync_g24_behind": 1,
    "sync_unknown": 0,
    "live_current": 42,
    "live_1_behind": 12,
    "live_l24_behind": 2,
    "live_inactive": 1
}
```

---

## Examples

### Complete Workflow

```python
from database_client import DBClientFactory

# Configure database connections
config = {
    'database': {
        'remote_type': 'mysql',
        'remote_config': {
            'host': 'localhost',
            'database': 'hash_db',
            'user': 'user',
            'password': 'password'
        },
        'core_type': 'mysql',
        'core_config': {
            'host': 'core.example.com',
            'database': 'core_db',
            'user': 'core_user',
            'password': 'core_password'
        },
        'pipeline_type': 'mssql',
        'pipeline_config': {
            'server': 'pipeline.example.com',
            'database': 'pipeline_db',
            'username': 'pipeline_user',
            'password': 'pipeline_password'
        }
    }
}

# Create database client
factory = DBClientFactory(config)
db = factory.create_client()

# Store hash information
hash_record = {
    'path': '/home/user/documents',
    'current_hash': 'abc123def456',
    'dirs': ['subfolder1', 'subfolder2'],
    'files': ['document1.txt', 'document2.pdf'],
    'links': ['shortcut1'],
    'target_hash': 'abc123def456',
    'session_id': 'scan_20240108_001'
}

success = db.insert_or_update_hash(hash_record)
print(f"Hash record {'stored' if success else 'failed'}")

# Log the operation
log_entry = {
    'summary_message': 'Hash record updated',
    'detailed_message': f'Updated hash for {hash_record["path"]}',
    'log_level': 'INFO',
    'session_id': 'scan_20240108_001'
}
log_id = db.put_log(log_entry)
print(f"Log entry created with ID: {log_id}")

# Check for priority updates
priority_paths = db.get_priority_updates()
for path in priority_paths:
    print(f"Priority update needed: {path}")

# Get dashboard metrics (if core DB is available)
try:
    dashboard = db.get_dashboard_content()
    print(f"System health: {dashboard['live_current']} sites online")
except NotImplementedError:
    print("Core database not configured")

# Check database health
health = db.health_check()
print(f"Database health: {health}")
```

### Batch Operations

```python
# Batch hash updates
hash_records = [
    {
        'path': '/home/user/documents',
        'current_hash': 'abc123def456',
        'files': ['doc1.txt', 'doc2.pdf'],
        'session_id': 'batch_001'
    },
    {
        'path': '/home/user/pictures',
        'current_hash': 'def456abc123',
        'files': ['pic1.jpg', 'pic2.png'],
        'session_id': 'batch_001'
    }
]

successful_updates = 0
for record in hash_records:
    if db.insert_or_update_hash(record):
        successful_updates += 1

print(f"Successfully updated {successful_updates} of {len(hash_records)} records")

# Batch log cleanup
old_logs = db.get_logs(older_than_days=30)
if old_logs:
    log_ids = [log['log_id'] for log in old_logs]
    deleted_count, failed_deletes = db.delete_log_entries(log_ids)
    print(f"Cleaned up {deleted_count} old log entries")
```

### Error Handling Example

```python
from database_client import DBClientFactory
import mysql.connector

try:
    config = {
        'database': {
            'remote_type': 'mysql',
            'remote_config': {
                'host': 'localhost',
                'database': 'hash_db',
                'user': 'user',
                'password': 'wrong_password'  # Intentionally wrong
            }
        }
    }
    
    factory = DBClientFactory(config)
    db = factory.create_client()
    
    # Try to perform an operation
    health = db.health_check()
    if not health['local_db']:
        print("Database connection failed")
        
except mysql.connector.Error as e:
    print(f"MySQL error: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Multi-Database Operations

```python
# Working with multiple database tiers
db = factory.create_client()

# Remote database operations
remote_record = db.get_hash_record('/home/user/documents')
if remote_record:
    print(f"Remote hash: {remote_record['current_hash']}")

# Core database operations
try:
    dashboard = db.get_dashboard_content()
    error_count = db.get_log_count_last_24h('ERROR')
    print(f"Dashboard shows {error_count} errors in last 24 hours")
except NotImplementedError:
    print("Core database not available")

# Pipeline database operations
try:
    pipeline_updates = db.get_pipeline_updates()
    official_sites = db.get_official_sites()
    print(f"Pipeline has {len(pipeline_updates)} updates for {len(official_sites)} sites")
except NotImplementedError:
    print("Pipeline database not available")
```

## Development

### Project Structure

```
database_client/
├── __init__.py                      # Package initialization
├── db_factory.py                    # Database client factory
├── db_implementation.py             # Main DBInstance implementation
├── db_interfaces.py                 # Abstract database interfaces
├── remote_mysql.py                  # MySQL remote implementation
├── remote_mssql.py                  # MSSQL remote implementation (untested)
├── remote_memory.py                 # In-memory implementation
├── core_mysql.py                    # MySQL core implementation
└── pipeline_mssql.py                # MSSQL pipeline implementation
```

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd database_client

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m unittest discover tests/ -v
```

### Dependencies

- `mysql-connector-python`: MySQL database connectivity
- `pyodbc`: MSSQL database connectivity
- `typing`: Type hints support (Python 3.5+)
- `contextlib`: Context manager support
- `json`: JSON data handling

### Adding New Database Implementations

1. Create a new implementation file (e.g., `remote_postgresql.py`)
2. Implement the appropriate interface (`RemoteDBConnection`, `CoreDBConnection`, or `PipelineDBConnection`)
3. Add the implementation to the factory mappings in `db_factory.py`
4. Update configuration documentation

## Testing

The project includes comprehensive unit tests using Python's `unittest` framework.

### Running Tests

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test file
python -m unittest tests.test_db_factory -v

# Run with coverage (if coverage is installed)
coverage run -m unittest discover tests/
coverage report -m
```

### Test Coverage

Tests cover:
- Database factory instantiation
- Connection management
- CRUD operations
- Error handling scenarios
- Configuration validation
- Multi-database operations

## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

## Version

Current version: 1.0.0

## Changelog

**v1.0.0 - 2025-01-08**

- Initial release of modularized Database Client package
- **Added:** DBClientFactory for configuration-driven database instantiation
- **Added:** Multi-tier database support (remote, core, pipeline)
- **Added:** MySQL implementations for remote and core operations
- **Added:** MSSQL implementation for pipeline operations
- **Added:** In-memory implementation for testing
- **Added:** Comprehensive interface definitions
- **Added:** Hash storage and retrieval operations
- **Added:** Logging and monitoring capabilities
- **Added:** Health check and diagnostic features
- **Added:** Data integrity validation
- **Added:** Full type annotations for better development experience

### Roadmap

- [ ] Add PostgreSQL database support
- [ ] Implement connection pooling for better performance
- [ ] Add database migration utilities
- [ ] Support for read replicas and load balancing
- [ ] Add database metrics and monitoring
- [ ] Implement caching layer for frequently accessed data
- [ ] Add support for database transactions
- [ ] Implement backup and recovery utilities

## Support

- **Issues**: Report bugs and request features by contacting the development team
- **Documentation**: Comprehensive API documentation available in this README
- **Examples**: Multiple usage examples provided in the Examples section

## Acknowledgments

- Built with `mysql-connector-python` for MySQL operations
- MSSQL support via `pyodbc` library
- Comprehensive logging using Python's built-in logging module
- Type annotations for better IDE support and code maintainability
- Factory pattern for flexible database instantiation
- Interface-based design for easy testing and extension

---

**Made with 😠 by the SquishyBadger Team**
Feel free to bring us a coffee from the cafeteria!