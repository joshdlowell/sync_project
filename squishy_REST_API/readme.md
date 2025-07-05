# SquishyBadger REST API

A containerized REST API for SquishyBadger that provides seamless integration between worker applications (such as integrity verification services) and both local and core SquishyBadger databases. Built with Python Flask and designed for production deployment.

## Table of Contents

- [Service Operation](#service-operation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
  - [RESTAPIFactory](#restapifactory)
  - [Database Client Package](#database-client-package-api-documentation)
    - [DBClient](#dbconnection-interface)
    - [CoreDBClient](#coredbconnection-interface)
- [Development](#development)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Project Status](#project-status)
- [Version and Change Log](#version)
- [Roadmap](#roadmap)
- [Support](#support)
- [Acknowledgments](#acknowledgments)

## Service Operation
The squishy-REST-API service requires serves as the central service for
accessing and updating the local and core databases. It requires several
enviroment variables (see [config](#configuration)). Once started it will: 
1. Listen for `GET` and `POST` requests at it's defined endpoints
2. Process serve and update data from the core and local databases.
3. Return results from database operations

## Quick Start
There is a quick start for all the services in the root README.md, if you want to start just the 
squishy REST API use the instructions below.
### Using Docker

#### Build the Container
```bash
docker build -t squishy-rest-api .
```

#### Run with Docker
```bash
docker run -d \
  --name squishy-rest-api \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e SITE_NAME=SIT0
  -p 5000:5000 \
  squishy-rest-api
```
### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd squishy-rest-api

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LOCAL_DB_TYPE: mysql
export LOCAL_MYSQL_HOST: mysql-squishy-db
export LOCAL_MYSQL_DATABASE: squishy_db
export LOCAL_MYSQL_PORT: 3306
export SITE_NAME: SIT0
export API_HOST: 0.0.0.0
export API_PORT: 5000
export DEBUG: False
export LOG_LEVEL: INFO
export LOCAL_MYSQL_USER: your_app_user
export LOCAL_MYSQL_PASSWORD: your_user_password
export API_SECRET_KEY: squishy_key_12345


# Run the application
python -m squishy_REST_API
```

## Configuration

### Required Environment Variables
| Variable               | Description              | Default Value |
|------------------------|--------------------------|---------------|
| `LOCAL_MYSQL_USER`     | MySQL username           | `None`        |
| `LOCAL_MYSQL_PASSWORD` | MySQL password           | `None`        |
| `API_SECRET_KEY`       | API session key          | `None`        |
| `SITE_NAME`            | Site id of current site  | `None`        |

### Other configurable Environment Variables
| Variable                | Description               | Default            |
|-------------------------|---------------------------|--------------------|
| `LOCAL_DB_TYPE`         | Type of storage to use    | `mysql`            |
| `LOCAL_MYSQL_HOST`      | MySQL hostname            | `mysql-squishy-db` |
| `LOCAL_MYSQL_DATABASE`  | MySQL database name       | `squishy_db`       |
| `LOCAL_MYSQL_PORT`      | MySQL server port         | `3306`             |
| `CORE_HOST`             | Hostname of core server   | `hqs0-drsl-t002`   |
| `CORE_TOP_LEVEL_DOMAIN` | Top level domain of core  | `home`             |
| `API_HOST`              | REST API address          | `0.0.0.0`          |
| `API_PORT`              | REST API port             | `5000`             |
| `DEBUG`                 | REST API debugging        | `False`            |
| `LOG_LEVEL`             | REST API logging level    | `'INFO'`           | 

### Non-configurable variables
| Variable              | Description                                 | Default            |
|-----------------------|---------------------------------------------|--------------------|
| `workers`             | number of gunicorn workers                  | `4`                |
| `worker_class`        | gunicorn request handling                   | `sync`             |
| `timeout`             | Time before resetting idle workers          | `30`               |
| `keepalive`           | Seconds to wait for requests                | `2`                |
| `max_requests`        | Maximum requests before worker reset        | `1000`             |
| `max_requests_jitter` | jitter tolerance to add to requests         | `100`              |
| `accesslog`           | log write to location (default syslog)      | `-`                |
| `errorlog`            | log write to location (default errorlog)    | `-`                |                
| `proc_name`           | The name given to the process in the system | `squishy_rest_api` | 
| `use_gunicorn`        | Run the application with gunicorn (not dev) | `True`             | 


### Connection Details

- **Host**: `localhost` (or container name in Docker networks)
- **Port**: `5000` (configurable via `API_PORT`)
- **Base URL**: `http://localhost:5000/api/`

## API Reference

# App Factory Package API Documentation

## Overview

The `app_factory` package provides a factory pattern implementation for creating Flask REST API applications with proper configuration, dependency injection, and route registration. It's designed to create web APIs for hash-based integrity checking systems.

## Installation

```python
from app_factory import RESTAPIFactory
```

## Quick Start

```python
# Create a Flask application
app = RESTAPIFactory.create_app()

# Run the application
if __name__ == '__main__':
    app.run()
```

## API Reference

### RESTAPIFactory

Main factory class for creating Flask REST API applications.

#### Methods

##### `create_app(test_config=None) -> Flask`

Creates and configures a Flask application instance with database connectivity and API routes.

**Parameters:**
- `test_config` (dict, optional): Configuration dictionary for testing. If None, uses default configuration.

**Returns:**
- `Flask`: Configured Flask application instance

**Configuration:**
- `DEBUG`: Debug mode flag (default: False)
- `TESTING`: Testing mode flag (default: False)
- `SECRET_KEY`: Application secret key (default: 'dev-key-change-in-production')

**Example:**
```python
from app_factory import RESTAPIFactory

# Create with default config
app = RESTAPIFactory.create_app()

# Create with test config
test_config = {
    'DEBUG': True,
    'TESTING': True,
    'SECRET_KEY': 'test-secret-key'
}
test_app = RESTAPIFactory.create_app(test_config)
```

---

## API Routes

The factory automatically registers the following REST API endpoints:

### Hash Table Operations

#### `GET /api/hashtable`

Retrieves a hash record by path.

**Query Parameters:**
- `path` (string, required): The file/directory path to retrieve

**Response:**
- **200 OK**: Hash record found
  ```json
  {
    "message": "Success",
    "data": {
      "path": "/example/path",
      "hash": "abc123...",
      "timestamp": "2023-01-01T00:00:00Z"
    }
  }
  ```
- **400 Bad Request**: Missing path parameter
- **404 Not Found**: Path not found

**Example:**
```bash
curl "http://localhost:5000/api/hashtable?path=/home/user/documents"
```

#### `POST /api/hashtable`

Inserts or updates a hash record.

**Request Body:**
```json
{
  "path": "/example/path",
  "hash": "abc123...",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

**Response:**
- **200 OK**: Record updated successfully
- **400 Bad Request**: Missing required 'path' field
- **500 Internal Server Error**: Database error

**Example:**
```bash
curl -X POST "http://localhost:5000/api/hashtable" \
  -H "Content-Type: application/json" \
  -d '{"path": "/home/user/file.txt", "hash": "abc123"}'
```

### Single Hash Operations

#### `GET /api/hash`

Retrieves only the hash value for a specific path.

**Query Parameters:**
- `path` (string, required): The file/directory path

**Response:**
- **200 OK**: Hash value found
  ```json
  {
    "message": "Success",
    "data": "abc123..."
  }
  ```
- **404 Not Found**: Path not found

**Example:**
```bash
curl "http://localhost:5000/api/hash?path=/home/user/documents"
```

### Timestamp Operations

#### `GET /api/timestamp`

Retrieves the latest timestamp for a path.

**Query Parameters:**
- `path` (string, required): The file/directory path

**Response:**
- **200 OK**: Timestamp found
  ```json
  {
    "message": "Success",
    "data": "2023-01-01T00:00:00Z"
  }
  ```
- **404 Not Found**: Path not found

**Example:**
```bash
curl "http://localhost:5000/api/timestamp?path=/home/user/documents"
```

### Priority Operations

#### `GET /api/priority`

Retrieves a list of directories that need to be updated based on their age.

**Response:**
- **200 OK**: Priority list retrieved
  ```json
  {
    "message": "Success",
    "data": ["/path/to/old/dir1", "/path/to/old/dir2"]
  }
  ```

**Example:**
```bash
curl "http://localhost:5000/api/priority"
```

### Health Check

#### `GET /api/lifecheck`

Checks the liveness of the API and database connection.

**Response:**
- **200 OK**: Service status
  ```json
  {
    "message": "Success",
    "data": {
      "api": true,
      "db": true
    }
  }
  ```

**Example:**
```bash
curl "http://localhost:5000/api/lifecheck"
```

---

## Error Handling

The application includes comprehensive error handling:

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **405 Method Not Allowed**: HTTP method not supported
- **500 Internal Server Error**: Server or database error

### Error Response Format

```json
{
  "message": "Error description"
}
```

### Registered Error Handlers

- **404 Handler**: Resource not found errors
- **500 Handler**: Internal server errors
- **General Exception Handler**: Catches all unhandled exceptions

---

## Module Structure

### api_routes.py

Contains route definitions and registration logic.

#### Functions

##### `register_routes(app: Flask, db_instance)`

Registers all API routes with the Flask application.

**Parameters:**
- `app` (Flask): Flask application instance
- `db_instance`: Database connection instance

##### `register_error_handlers(app: Flask)`

Registers error handlers with the Flask application.

**Parameters:**
- `app` (Flask): Flask application instance

---

## Dependencies

The package requires:
- Flask
- squishy_REST_API (for logging and configuration)
- squishy_REST_API.database_client (for database connectivity)

---

## Configuration

The application uses configuration from the `squishy_REST_API.config` module:

```python
{
    'debug': False,
    'secret_key': 'dev-key-change-in-production'
}
```

---

## Logging

All operations are logged using the `squishy_REST_API.logger` module:

- Debug level: Route access and parameters
- Info level: Successful operations and configuration
- Warning level: Client errors (400-level)
- Error level: Server errors (500-level)

---

## Examples

### Basic Flask Application

```python
from app_factory import RESTAPIFactory

# Create application
app = RESTAPIFactory.create_app()

# Run in development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Production Deployment

```python
from app_factory import RESTAPIFactory

# Create application with production config
production_config = {
    'DEBUG': False,
    'SECRET_KEY': 'your-production-secret-key'
}

app = RESTAPIFactory.create_app(production_config)

# Deploy with WSGI server (e.g., Gunicorn)
# gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Testing Setup

```python
import pytest
from app_factory import RESTAPIFactory

@pytest.fixture
def client():
    test_config = {
        'TESTING': True,
        'DEBUG': True
    }
    app = RESTAPIFactory.create_app(test_config)
    
    with app.test_client() as client:
        yield client

def test_lifecheck(client):
    response = client.get('/api/lifecheck')
    assert response.status_code == 200
```

### Custom Database Integration

```python
from app_factory.api_routes import register_routes
from flask import Flask

# Create custom app with different database
app = Flask(__name__)
custom_db = MyCustomDatabase()

register_routes(app, custom_db)
```
---

## Database Client Package API Documentation

The `database_client` package provides a flexible database abstraction layer with support for multiple database backends including MySQL, MS SQL Server, and in-memory storage. It offers a unified interface for hash table operations and logging functionality.

## Installation

```python
from database_client import DBClient
from database_client import CoreDBClient
```

## Quick Start

```python
# Create a database client
db_client = DBClient()

# Get database connection (uses configuration)
db = db_client.database_client

# Insert or update a hash record
record = {
    'path': '/home/user/file.txt',
    'current_hash': 'abc123...',
    'timestamp': 1234567890
}
success = db.insert_or_update_hash(record)
```

```python
# Create a core database client
core_db_client = CoreDBClient()

# Get database connection (uses configuration)
db = core_db_client.database_client

# Get all log entries in the last 30 days from the logs table
logs_list = db.get_recent_logs()
```

## API Reference

### DBClient

Main factory class for creating database connections.

#### Properties

##### `database_client` (property)
```python
@property
def database_client(db_type: str = None) -> DBConnection
```

Returns a configured database connection instance.

**Parameters:**
- `db_type` (str, optional): Database type override. If not provided, uses configuration.

**Returns:**
- `DBConnection`: Database connection instance

**Example:**
```python
db_client = DBClient()
db = db_client.database_client
```

#### Methods

##### `create_db_service(db_type: str) -> DBConnection`

Creates a database instance using configuration.

**Parameters:**
- `db_type` (str): Database type ('mysql', 'mssql', or 'internal')

**Returns:**
- `DBConnection`: Database connection instance

**Raises:**
- `ValueError`: When database configuration values are invalid or missing
- `ConnectionError`: When unable to establish database connection
- `Exception`: For any other unexpected errors during database creation

**Supported Database Types:**
- `'mysql'`: MySQL database connection
- `'internal'`: In-memory non-persistent storage
- `'mssql'`: MS SQL Server connection (if implemented)

**Required Configuration (MySQL):**
- `db_host`: Database host
- `db_name`: Database name
- `db_user`: Database username
- `db_password`: Database password
- `db_port`: Database port (optional, defaults to 3306)

**Example:**
```python
db_client = DBClient()
mysql_db = db_client.create_db_service('mysql')
memory_db = db_client.create_db_service('internal')
```

---

## DBConnection Interface

Abstract base class defining the database interface. All database implementations inherit from this class.

### Hash Operations

#### `insert_or_update_hash(record: Dict[str, Any]) -> bool`

Inserts new record or updates existing one. Logs changes discovered to database.

**Parameters:**
- `record` (Dict[str, Any]): Dictionary of hashtable column:value keypairs

**Returns:**
- `bool`: True if successful, False if an error occurred

**Raises:**
- `ValueError`: If required parameters are not provided

**Example:**
```python
record = {
    'path': '/home/user/documents',
    'current_hash': 'a1b2c3d4e5f6...',
    'timestamp': 1640995200,
    'dirs': ['subdir1', 'subdir2'],
    'files': ['file1.txt', 'file2.txt'],
    'links': ['symlink1']
}
success = db.insert_or_update_hash(record)
```

#### `get_hash_record(path: str) -> Optional[Dict[str, Any]]`

Retrieves a complete hash record by path.

**Parameters:**
- `path` (str): Path to retrieve

**Returns:**
- `Optional[Dict[str, Any]]`: Dictionary with record data or None if not found

**Example:**
```python
record = db.get_hash_record('/home/user/documents')
if record:
    print(f"Hash: {record['current_hash']}")
    print(f"Timestamp: {record['timestamp']}")
```

#### `get_single_hash_record(path: str) -> Optional[str]`

Retrieves only the current hash value for a path.

**Parameters:**
- `path` (str): Path to retrieve hash for

**Returns:**
- `Optional[str]`: Hash value as string or None if not found

**Example:**
```python
hash_value = db.get_single_hash_record('/home/user/file.txt')
if hash_value:
    print(f"Current hash: {hash_value}")
```

#### `get_single_timestamp(path: str) -> Optional[int]`

Retrieves only the timestamp for a path's hash record.

**Parameters:**
- `path` (str): Path to retrieve timestamp for

**Returns:**
- `Optional[int]`: Timestamp value as int or None if not found

**Example:**
```python
timestamp = db.get_single_timestamp('/home/user/file.txt')
if timestamp:
    print(f"Last updated: {timestamp}")
```

### Update Management

#### `get_oldest_updates(root_path: str, percent: int = 10) -> List[str]`

Retrieves directories that need updating based on their age.

**Parameters:**
- `root_path` (str): Root directory to start from
- `percent` (int, optional): Percentage of directories to return (default: 10%)

**Returns:**
- `List[str]`: List of directory paths that need updating

**Example:**
```python
# Get oldest 20% of directories for updating
old_dirs = db.get_oldest_updates('/home/user', percent=20)
for dir_path in old_dirs:
    print(f"Needs update: {dir_path}")
```

#### `get_priority_updates() -> List[str]`

Retrieves directories where target hash doesn't match current hash.

**Returns:**
- `List[str]`: List of directory paths that need rechecking

**Example:**
```python
priority_dirs = db.get_priority_updates()
for dir_path in priority_dirs:
    print(f"Priority update needed: {dir_path}")
```

### Logging Operations

#### `put_log(args_dict: Dict) -> Optional[int]`

Inserts a log entry into the database.

**Parameters:**
- `args_dict` (Dict): Dictionary containing log entry data

**Returns:**
- `Optional[int]`: Log ID number if successful, None if error occurred

**Example:**
```python
log_entry = {
    'level': 'INFO',
    'message': 'Hash computed successfully',
    'path': '/home/user/file.txt',
    'timestamp': 1640995200
}
log_id = db.put_log(log_entry)
if log_id:
    print(f"Log entry created with ID: {log_id}")
```

#### `get_logs(limit: Optional[int] = None, offset: int = 0, order_by: str = "timestamp", order_direction: str = "DESC") -> List[Dict[str, Any]]`

Retrieves log entries from the database with pagination and ordering.

**Parameters:**
- `limit` (Optional[int]): Maximum number of records to return (None for all)
- `offset` (int): Number of records to skip for pagination (default: 0)
- `order_by` (str): Column name to order by (default: 'timestamp')
- `order_direction` (str): Sort direction 'ASC' or 'DESC' (default: 'DESC')

**Returns:**
- `List[Dict[str, Any]]`: List of log entry dictionaries

**Raises:**
- `ValueError`: If invalid parameters are provided

**Example:**
```python
# Get latest 50 log entries
recent_logs = db.get_logs(limit=50)

# Get logs with pagination
page_2_logs = db.get_logs(limit=25, offset=25)

# Get oldest logs first
old_logs = db.get_logs(limit=10, order_direction='ASC')
```

#### `delete_log_entry(log_id: int) -> bool`

Removes a log entry from the database.

**Parameters:**
- `log_id` (int): Log entry ID to be removed

**Returns:**
- `bool`: True if deleted successfully, False if not found or error occurred

**Example:**
```python
success = db.delete_log_entry(123)
if success:
    print("Log entry deleted successfully")
```

### Health Check

#### `life_check() -> bool`

Verifies that the database is active and responsive.

**Returns:**
- `bool`: True if database is active and responsive, False otherwise

**Example:**
```python
if db.life_check():
    print("Database is healthy")
else:
    print("Database connection issues detected")
```

---

## Database Implementations

### MYSQLConnection

MySQL database implementation of the `DBConnection` interface.

**Constructor:**
```python
MYSQLConnection(
    host: str,
    database: str,
    user: str,
    password: str,
    port: int = 3306
)
```

**Features:**
- Full SQL database persistence
- ACID compliance
- Connection pooling
- Transaction support

### LocalMemoryConnection

In-memory database implementation for testing and development.

**Features:**
- Non-persistent storage
- Fast operations
- No external dependencies
- Perfect for testing

### LocalMSSQLConnection

Microsoft SQL Server implementation (if available).

**Features:**
- Enterprise-grade database support
- Windows authentication support
- Advanced querying capabilities

---

## CoreDBConnection Interface

Abstract base class defining the database interface for core site operations. This interface provides specialized methods for core sites that need to monitor and manage distributed hash integrity systems.

### Dashboard Operations

#### `get_dashboard_content() -> Dict[str, Any]`

Retrieves comprehensive dashboard metrics for site monitoring system.

Executes a complex query to gather site synchronization status, live status, and critical error counts across all sites in the site_list. Uses current and previous baselines from state_history to categorize sync status.

**Returns:**
- `Dict[str, Any]`: Dashboard metrics dictionary containing:
  - `crit_error_count` (int): Critical errors in last 24 hours
  - `hash_record_count` (int): Record count from current baseline
  - `sync_current` (int): Sites with current baseline sync
  - `sync_1_behind` (int): Sites one baseline behind
  - `sync_l24_behind` (int): Sites with hash from last 24 hours
  - `sync_g24_behind` (int): Sites with hash older than 24 hours
  - `sync_unknown` (int): Sites with unknown baseline hash
  - `live_current` (int): Sites active in last 35 minutes
  - `live_1_behind` (int): Sites active between 35m-24h ago
  - `live_l24_behind` (int): Sites active in last 24 hours
  - `live_inactive` (int): Sites inactive for over 24 hours

**Note:**
Returns dictionary with zero values for all metrics if query fails. Only includes sites that exist in the authoritative site_list table.

**Example:**
```python
core_db = core_db_client.database_client
dashboard_data = core_db.get_dashboard_content()

print(f"Sites in sync: {dashboard_data['sync_current']}")
print(f"Critical errors: {dashboard_data['crit_error_count']}")
print(f"Live sites: {dashboard_data['live_current']}")
```

### Logging Operations

#### `get_recent_logs() -> List[Dict[str, Any]]`

Retrieves all log entries from the last 30 days.

**Returns:**
- `List[Dict[str, Any]]`: List of log record dictionaries from the last 30 days, or empty list if no records found or an error occurred

**Example:**
```python
recent_logs = core_db.get_recent_logs()
print(f"Found {len(recent_logs)} log entries in the last 30 days")

for log in recent_logs:
    print(f"{log['timestamp']}: {log['level']} - {log['message']}")
```

#### `get_log_count_last_24h(log_level: str) -> int`

Counts log entries for a specific log level in the last 24 hours.

This method counts log entries from the local database for a given log level that occurred within the last 24 hours based on unix timestamp.

**Parameters:**
- `log_level` (str): The log level to count. Must be one of: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

**Returns:**
- `int`: Count of matching log records in the last 24 hours. Returns 0 if no records found or on error.

**Raises:**
- `ValueError`: If invalid log_level is provided

**Example:**
```python
# Count critical errors in last 24 hours
critical_count = core_db.get_log_count_last_24h('CRITICAL')
print(f"Critical errors in last 24h: {critical_count}")

# Count all warning levels
warning_count = core_db.get_log_count_last_24h('WARNING')
error_count = core_db.get_log_count_last_24h('ERROR')
total_issues = warning_count + error_count + critical_count
print(f"Total issues in last 24h: {total_issues}")
```

### Statistics Operations

#### `get_hash_record_count() -> int`

Retrieves the total count of records in the hashtable.

**Returns:**
- `int`: Total count of records in the hashtable, or 0 if an error occurred

**Example:**
```python
total_records = core_db.get_hash_record_count()
print(f"Total hash records in database: {total_records}")
```

---

## Core Site Database Implementation

### CoreMySQLConnection

MySQL database implementation of the `CoreDBConnection` interface for core site operations.

**Constructor:**
```python
CoreMySQLConnection(
    host: str,
    database: str,
    user: str,
    password: str,
    port: int = 3306
)
```

**Features:**
- Specialized queries for multi-site monitoring
- Dashboard metrics aggregation
- Site synchronization status tracking
- Advanced log analysis capabilities

**Example:**
```python
from database_client import CoreMySQLConnection

# Create core site database connection
core_db = CoreMySQLConnection(
    host="core-db-server",
    database="integrity_core",
    user="core_admin",
    password="secure_password",
    port=3306
)

# Get dashboard overview
dashboard = core_db.get_dashboard_content()
print(f"System overview: {dashboard['sync_current']} sites in sync")
```

---

## Core Site Usage Examples

### Dashboard Monitoring

```python
from database_client import DBClient

# Create core site client
core_client = DBClient()
core_db = core_client.create_db_service('core_mysql')

# Get comprehensive dashboard data
dashboard = core_db.get_dashboard_content()

# Display sync status
print("=== Site Synchronization Status ===")
print(f"Current sync: {dashboard['sync_current']}")
print(f"1 baseline behind: {dashboard['sync_1_behind']}")
print(f"Last 24h sync: {dashboard['sync_l24_behind']}")
print(f"Over 24h behind: {dashboard['sync_g24_behind']}")
print(f"Unknown status: {dashboard['sync_unknown']}")

# Display live status
print("\n=== Site Live Status ===")
print(f"Currently active: {dashboard['live_current']}")
print(f"Recently active: {dashboard['live_1_behind']}")
print(f"Last 24h active: {dashboard['live_l24_behind']}")
print(f"Inactive: {dashboard['live_inactive']}")

# Display system health
print(f"\n=== System Health ===")
print(f"Critical errors (24h): {dashboard['crit_error_count']}")
print(f"Total hash records: {dashboard['hash_record_count']}")
```

### Log Analysis

```python
# Analyze recent system activity
recent_logs = core_db.get_recent_logs()
print(f"Total logs in last 30 days: {len(recent_logs)}")

# Count different log levels in last 24 hours
log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
print("\n=== Log Level Summary (Last 24h) ===")
for level in log_levels:
    count = core_db.get_log_count_last_24h(level)
    print(f"{level}: {count}")

# Check for critical issues
critical_errors = core_db.get_log_count_last_24h('CRITICAL')
if critical_errors > 0:
    print(f"\n⚠️  {critical_errors} critical errors need attention!")
```

### System Statistics

```python
# Get system scale metrics
hash_count = core_db.get_hash_record_count()
recent_logs = core_db.get_recent_logs()

print("=== System Scale ===")
print(f"Total hash records: {hash_count:,}")
print(f"Recent log entries: {len(recent_logs):,}")

# Calculate activity rate
if recent_logs:
    daily_log_rate = len(recent_logs) / 30
    print(f"Average daily log rate: {daily_log_rate:.1f} entries/day")
```

---

## Core Site Configuration

Core site database connections require additional configuration:

### Core MySQL Configuration
```python
# Required for core sites
db_type = "core_mysql"
db_host = "core-database-server"
db_name = "integrity_core_db"
db_user = "core_admin"
db_password = "secure_core_password"

# Optional
db_port = 3306
```

The core site interface is designed for centralized monitoring and management of distributed hash integrity systems, providing specialized metrics and analytics not available in the standard `DBConnection` interface.

## Configuration

The package uses the `squishy_REST_API.config` module for configuration. Required configuration keys depend on the database type:

### MySQL Configuration
```python
# Required
db_type = "mysql"
db_host = "localhost"
db_name = "integrity_db"
db_user = "username"
db_password = "password"

# Optional
db_port = 3306
```

### Internal Memory Configuration
```python
db_type = "internal"
```

---

## Error Handling

The package includes comprehensive error handling:

- **Configuration Errors**: Missing or invalid configuration values
- **Connection Errors**: Database connection failures
- **Query Errors**: SQL execution failures
- **Data Validation**: Invalid parameter checking

All errors are logged using the `squishy_REST_API.logger` module.

---

## Examples

### Basic Usage

```python
from database_client import DBClient

# Create client and get database connection
db_client = DBClient()
db = db_client.database_client

# Check database health
if not db.life_check():
    print("Database is not responding")
    exit(1)

# Store hash information
record = {
    'path': '/important/file.txt',
    'current_hash': 'sha1hash...',
    'timestamp': 1640995200
}

if db.insert_or_update_hash(record):
    print("Hash stored successfully")

# Retrieve hash
hash_value = db.get_single_hash_record('/important/file.txt')
print(f"Stored hash: {hash_value}")
```

### Logging Example

```python
# Add log entry
log_data = {
    'level': 'WARNING',
    'message': 'Hash mismatch detected',
    'path': '/suspicious/file.txt',
    'details': 'Expected: abc123, Got: def456'
}

log_id = db.put_log(log_data)

# Retrieve recent logs
recent_logs = db.get_logs(limit=10)
for log in recent_logs:
    print(f"{log['timestamp']}: {log['level']} - {log['message']}")

# Clean up processed logs
if log_id:
    db.delete_log_entry(log_id)
```

### Update Management

```python
# Get directories that need updating
old_dirs = db.get_oldest_updates('/home/data', percent=15)
priority_dirs = db.get_priority_updates()

# Process updates
all_updates = old_dirs + priority_dirs
for dir_path in all_updates:
    print(f"Scheduling update for: {dir_path}")
```

### Different Database Types

```python
# Use MySQL
mysql_client = DBClient()
mysql_db = mysql_client.create_db_service('mysql')

# Use in-memory for testing
test_client = DBClient()
test_db = test_client.create_db_service('internal')

# Both have the same interface
for db in [mysql_db, test_db]:
    if db.life_check():
        print("Database is ready")
```

---

## Development

### Project Structure

```
squishy_REST_API/
├── core.py                         # Application entry point
├── app_factory/
│   ├── api_routes.py               # API endpoint definitions
│   ├── gui_routes.py               # web-gui endpoint definitions
│   └── app_factory.py              # Flask application factory
├── configuration/                  # Application configurations
│   ├── config.py                   # Main configuration
│   └── logging_config.py           # System logging configuration
├── database_client/                # Database interface implementations
│   ├── db_bootstrap.py             # Create and configure db implementations
│   ├── core_site_DB_interface.py   # Abstract interface
│   ├── core_site_mysql.py          # MySQL implementation
│   ├── local_DB_interface.py       # Abstract interface
│   ├── local_memory.py             # In-memory implementation
│   ├── local_mysql.py              # MySQL implementation
│   └── local_mssql_untested.py     # MSSQL Server (experimental)
├── web/                            # Web-gui assets
│   ├── static/                     # static web page elements
│   └── templates/                  # flask web page templates
├── tests/                          # Test suite
│   ├── test_api_and_gui_routes.py  # API endpoint tests
│   ├── test_core_db_client.py      # Database tests
│   └── test_local_db_client.py     # Database tests
├── requirements.txt                # Python dependencies
└── README.md
```

### Local Development Setup

1. **Prerequisites**: Python 3.12+, MySQL 8.0+
2. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Database Setup**: Ensure MySQL is running with proper credentials
4. **Environment**: Set required environment variables
5. **Run**: `python -m squishy_REST_API`

## Testing

The project includes comprehensive unit and integration tests using Python's `unittest` framework. Tests cover:

- API endpoint functionality
- Database connection interfaces
- Error handling and edge cases
- Configuration validation

Run tests with detailed output:
```bash
python -m unittest discover squishy_REST_API/tests/ -v
```

## Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (missing/invalid parameters)
- **404**: Resource Not Found
- **405**: Method Not Allowed
- **500**: Internal Server Error

### Common Error Messages
- `"Path not found"`: Requested resource doesn't exist
- `"path required but not found in your request json"`: Missing required field
- `"Database error, see DB logs"`: Internal database issue
- `"root_path parameter is required"`: Missing query parameter

## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

## Version

Current version: 2.0.0

## Changelog

**v2.0.0 - 2025-07-03**

-   **Added:** Web-GUI for core sites
-   **Added:** core site DB interface for Core only operations
-   **Modified:** Changed app factory to create core assets if and only if current site is core

**v1.0.0 - 2025-06-26**

-   Baseline of current project state.

### Roadmap
- [ ] Comprehensive logging and monitoring
- [ ] Web GUI to easily access status
- [ ] Enhanced authentication and authorization
- [ ] Rate limiting implementation
- [ ] Performance optimization
- [ ] Additional database backend support

## Support

- **Issues**: Report bugs and request features by contacting us
- **Documentation**: Detailed API docs available in `configuration/README.md` and `storage_service/README.md`

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) web framework
- Database connectivity powered by MySQL
- Containerization with Docker
- Testing framework: Python unittest

---

**Made with 😠 by the SquishyBadger Team**
Feel free to bring us a coffee from the cafeteria!