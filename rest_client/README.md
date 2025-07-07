# RestClient Package

A robust and modular REST client library for interacting with hash storage APIs. This package provides comprehensive HTTP client functionality with built-in retry logic, request validation, and error handling specifically designed for hash storage and integrity verification operations.

## Table of Contents

- [Package Overview](#package-overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
  - [RestClient](#restclient)
  - [RestProcessor](#restprocessor)
  - [HttpClient](#httpclient)
  - [HashInfoValidator](#hashinfovalidator)
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

The RestClient package provides a comprehensive solution for REST API interactions with hash storage systems. It offers modular components for HTTP communication, request validation, and response processing with robust error handling and retry mechanisms.

Key features:
- **Modular Design**: Separate components for HTTP client, validation, and processing
- **Robust Error Handling**: Comprehensive retry logic with exponential backoff
- **Type Safety**: Full type annotations for better development experience
- **Validation**: Built-in request validation for hash information
- **Logging**: Comprehensive logging for debugging and monitoring
- **Configuration**: Environment-based configuration management

## Quick Start

```python
from rest_client import RestClient

# Create a REST client instance
client = RestClient()
processor = client.create_rest_connector("https://api.example.com")

# Store hash information
hash_info = {
    "/path/to/file": {
        "target_hash": "abc123def456",
        "current_hash": "abc123def456",
        "dirs": ["subdir1", "subdir2"],
        "files": ["file1.txt", "file2.pdf"],
        "links": ["symlink1"]
    }
}

# Send hash information to API
successful_updates = processor.put_hashtable(hash_info)
print(f"Successfully stored {successful_updates} hash entries")

# Retrieve hash information
hashtable = processor.get_hashtable("/path/to/file")
if hashtable:
    print(f"Current hash: {hashtable.get('current_hash')}")
```

## Installation

```python
# Import the package
from rest_client import RestClient
from rest_client.rest_processor import RestProcessor
from rest_client.hash_info_validator import HashInfoValidator
```

## Configuration

### Environment Variables

| Variable         | Description                    | Default            |
|------------------|--------------------------------|--------------------|
| `REST_API_HOST`  | REST API hostname              | `squishy-rest-api` |
| `REST_API_PORT`  | REST API port                  | `5000`             |
| `LOG_LEVEL`      | Logging level                  | `INFO`             |

### Configuration Properties

| Property         | Description                              | Default |
|------------------|------------------------------------------|---------|
| `max_retries`    | Maximum number of retry attempts         | `3`     |
| `retry_delay`    | Delay between retries (seconds)          | `5`     |
| `long_delay`     | Extended delay between retry cycles      | `30`    |

### Configuration Access

```python
from rest_client.configuration import config

# Access configuration values
api_url = config.rest_api_url
max_retries = config.get('max_retries')
```

## API Reference

### RestClient

Main factory class for creating REST client components.

#### Methods

##### `create_rest_connector(url: str) -> RestProcessor`

Creates a fully configured `RestProcessor` instance.

**Parameters:**
- `url` (str): The REST API URL endpoint for hash storage operations

**Returns:**
- `RestProcessor`: Configured REST processor instance

**Raises:**
- `TypeError`: If url is not a string
- `ValueError`: If url is empty or contains only whitespace
- `ImportError`: If required dependencies are not available

**Example:**
```python
from rest_client import RestClient

client = RestClient()
processor = client.create_rest_connector("https://api.example.com")
```

---

### RestProcessor

Core class for REST API interactions and hash storage operations.

#### Constructor

```python
RestProcessor(
    rest_api_url: str,
    http_client: HttpClient,
    validator: HashInfoValidator = None
)
```

**Parameters:**
- `rest_api_url` (str): URL for the REST API
- `http_client` (HttpClient): HTTP client for making requests
- `validator` (HashInfoValidator, optional): Validator for hash information

#### Methods

##### `put_hashtable(hash_info: dict) -> int`

Stores hash information in the database via REST API.

**Parameters:**
- `hash_info` (dict): Dictionary containing hash information for files and directories

**Returns:**
- `int`: Number of successfully stored hash entries

**Example:**
```python
hash_info = {
    "/path/to/file": {
        "target_hash": "abc123",
        "current_hash": "abc123",
        "dirs": ["subdir1", "subdir2"],
        "files": ["file1.txt", "file2.txt"],
        "links": ["symlink1"]
    }
}
successful_count = processor.put_hashtable(hash_info)
```

##### `get_hashtable(path: str) -> dict | None`

Retrieves the complete hash table for a specific path.

**Parameters:**
- `path` (str): The path to get the hash table for

**Returns:**
- `dict | None`: Hash table dictionary, or None if not found

**Example:**
```python
hashtable = processor.get_hashtable("/path/to/directory")
if hashtable:
    print(f"Directories: {hashtable.get('dirs', [])}")
    print(f"Files: {hashtable.get('files', [])}")
```

##### `get_single_hash(path: str) -> str | None`

Retrieves the hash value for a specific path.

**Parameters:**
- `path` (str): The path to get the hash for

**Returns:**
- `str | None`: Hash value as string, or None if not found

**Example:**
```python
hash_value = processor.get_single_hash("/path/to/file")
if hash_value:
    print(f"Hash: {hash_value}")
```

##### `get_oldest_updates(root_path: str, percent: int = 10) -> list[str]`

Gets directories that need updates based on their age.

**Parameters:**
- `root_path` (str): Root directory to start from
- `percent` (int, optional): Percentage of directories to return (default: 10)

**Returns:**
- `list[str]`: List of directory paths needing updates

**Example:**
```python
old_dirs = processor.get_oldest_updates("/home/user", percent=20)
for dir_path in old_dirs:
    print(f"Needs update: {dir_path}")
```

##### `get_single_timestamp(path: str) -> float | None`

Retrieves the timestamp for a specific path.

**Parameters:**
- `path` (str): The path to get the timestamp for

**Returns:**
- `float | None`: Timestamp as float, or None if not found

##### `get_priority_updates() -> list | None`

Gets paths that need priority updates.

**Returns:**
- `list | None`: List of paths needing priority updates, or None if not found

**Example:**
```python
priority_paths = processor.get_priority_updates()
if priority_paths:
    for path in priority_paths:
        print(f"Priority update needed: {path}")
```

##### `get_lifecheck() -> dict | None`

Retrieves the liveness status of the REST API and database.

**Returns:**
- `dict | None`: Dictionary with boolean values for 'api' and 'db' keys, or None if error occurs

##### `put_log(message: str, site_id: str = None, timestamp: int = None, detailed_message: str = None, log_level: str = None, session_id: str = None) -> int`

Stores log information in the database.

**Parameters:**
- `message` (str): The log message (required)
- `site_id` (str, optional): Site identifier
- `timestamp` (int, optional): Timestamp for the log entry
- `detailed_message` (str, optional): Detailed version of the message
- `log_level` (str, optional): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `session_id` (str, optional): Session ID for grouping log entries

**Returns:**
- `int`: 1 if successful, 0 if failed

##### `find_orphaned_entries() -> list | None`

Gets database entries that aren't listed by a parent.

**Returns:**
- `list | None`: List of orphaned paths, or None if not found

##### `find_untracked_children() -> list | None`

Gets children claimed by a parent but not tracked in the database.

**Returns:**
- `list | None`: List of untracked paths, or None if not found

##### `get_pipeline_updates() -> list | None`

Gets updates from the pipeline that haven't been processed.

**Returns:**
- `list | None`: List of pipeline update paths, or None if not found

##### `consolidate_logs() -> bool | None`

Triggers log consolidation via REST API.

**Returns:**
- `bool | None`: True if successful, None otherwise

##### `collect_logs_for_shipping() -> list[dict[str, Any]] | None`

Retrieves log entries ready for shipping to core database.

**Returns:**
- `list[dict[str, Any]] | None`: List of log entries, or None if not found

##### `collect_logs_older_than(days: int) -> list[dict[str, Any]] | None`

Retrieves log entries older than specified days.

**Parameters:**
- `days` (int): Number of days threshold

**Returns:**
- `list[dict[str, Any]] | None`: List of old log entries, or None if not found

##### `delete_log_entries(log_ids: list[int]) -> Tuple[bool, list]`

Deletes multiple log entries by their IDs.

**Parameters:**
- `log_ids` (list[int]): List of log entry IDs to delete

**Returns:**
- `Tuple[bool, list]`: Success status and response data

---

### HttpClient

Abstract base class for HTTP operations.

#### Methods

##### `post(url: str, json_data: dict) -> Tuple[int, Any]`

Sends a POST request.

**Parameters:**
- `url` (str): Target URL
- `json_data` (dict): JSON data to send

**Returns:**
- `Tuple[int, Any]`: Status code and response content

##### `get(url: str, params: dict = None) -> Tuple[int, Any]`

Sends a GET request.

**Parameters:**
- `url` (str): Target URL
- `params` (dict, optional): Query parameters

**Returns:**
- `Tuple[int, Any]`: Status code and response content

##### `delete(url: str, json_data: dict = None) -> Tuple[int, Any]`

Sends a DELETE request.

**Parameters:**
- `url` (str): Target URL
- `json_data` (dict, optional): JSON data to send

**Returns:**
- `Tuple[int, Any]`: Status code and response content

---

### RequestsHttpClient

Concrete implementation of `HttpClient` using the `requests` library.

#### Constructor

```python
RequestsHttpClient()
```

Initializes with retry configuration from the config module.

#### Features

- **Automatic Retries**: Configurable retry attempts with exponential backoff
- **Timeout Handling**: 30-second timeout for all requests
- **Connection Recovery**: Handles connection errors gracefully
- **Comprehensive Logging**: Detailed logging for debugging

**Example:**
```python
from rest_client.http_client import RequestsHttpClient

client = RequestsHttpClient()
status, response = client.get("https://api.example.com/data")

if status == 200:
    print("Success:", response)
else:
    print(f"Error {status}: {response}")
```

---

### HashInfoValidator

Validates hash information data structures before sending to REST API.

#### Class Attributes

- `VALID_KEYS`: Set of valid keys for hash info items
- `REQUIRED_KEYS`: Set of required keys for hash info items

#### Methods

##### `validate(hash_info: dict) -> list`

Validates hash information and returns validation errors.

**Parameters:**
- `hash_info` (dict): Hash information dictionary to validate

**Returns:**
- `list`: List of validation error messages

**Example:**
```python
from rest_client.hash_info_validator import HashInfoValidator

validator = HashInfoValidator()
hash_info = {"/path": {"target_hash": "abc123"}}
errors = validator.validate(hash_info)

if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

---

## Error Handling

The package provides comprehensive error handling:

### HTTP Status Codes

- **200**: Success
- **207**: Partial success (multi-status)
- **404**: Resource not found
- **408**: Request timeout
- **503**: Service unavailable
- **Other codes**: Various HTTP errors

### Exception Handling

- `requests.exceptions.Timeout`: Request timeout
- `requests.exceptions.ConnectionError`: Connection issues
- `requests.exceptions.RequestException`: General request failures
- `ValueError`: JSON decode errors
- `TypeError`: Type validation errors
- `ConfigError`: Configuration validation errors

### Logging

All operations are logged with appropriate levels:

- **DEBUG**: Detailed operation information
- **INFO**: General status updates
- **WARNING**: Recoverable errors and retries
- **ERROR**: Validation errors and failed operations
- **CRITICAL**: Network errors and system issues

---

## Data Structures

### Hash Info Structure

```python
{
    "path": {
        "target_hash": "required_hash_value",
        "current_hash": "optional_current_hash",
        "current_dtg_latest": "optional_timestamp",
        "dirs": ["list", "of", "directories"],
        "files": ["list", "of", "files"],
        "links": ["list", "of", "symlinks"],
        "session_id": "optional_session_id"
    }
}
```

### API Response Structure

```python
{
    "data": "response_data",
    "message": "status_message"
}
```

---

## Examples

### Complete Workflow

```python
from rest_client import RestClient

# Initialize client
client = RestClient()
processor = client.create_rest_connector("https://api.example.com")

# Prepare hash information
hash_info = {
    "/home/user/documents": {
        "target_hash": "abc123def456",
        "current_hash": "abc123def456",
        "dirs": ["subfolder1", "subfolder2"],
        "files": ["document1.txt", "document2.pdf"],
        "links": ["shortcut1"]
    }
}

# Store hash information
successful_count = processor.put_hashtable(hash_info)
print(f"Successfully stored {successful_count} hash entries")

# Retrieve hash information
retrieved = processor.get_hashtable("/home/user/documents")
if retrieved:
    print(f"Current hash: {retrieved.get('current_hash')}")
    print(f"Contains {len(retrieved.get('files', []))} files")

# Get directories needing updates
old_dirs = processor.get_oldest_updates("/home/user", percent=15)
for path in old_dirs:
    print(f"Directory needs update: {path}")

# Log an operation
log_result = processor.put_log(
    message="Hash update completed",
    detailed_message="Updated 5 directories successfully",
    log_level="INFO"
)
print(f"Log entry {'created' if log_result else 'failed'}")
```

### Custom HTTP Client

```python
from rest_client.http_client import HttpClient
from rest_client.rest_processor import RestProcessor
from rest_client.hash_info_validator import HashInfoValidator

class CustomHttpClient(HttpClient):
    def post(self, url: str, json_data: dict):
        # Custom POST implementation
        pass
    
    def get(self, url: str, params: dict = None):
        # Custom GET implementation
        pass
    
    def delete(self, url: str, json_data: dict = None):
        # Custom DELETE implementation
        pass

# Use custom client
custom_client = CustomHttpClient()
validator = HashInfoValidator()
processor = RestProcessor("https://api.example.com", custom_client, validator)
```

### Error Handling Example

```python
from rest_client import RestClient
from rest_client.configuration import logger

try:
    client = RestClient()
    processor = client.create_rest_connector("https://api.example.com")
    
    # Invalid hash info - missing required field
    hash_info = {"/invalid": {"dirs": ["subdir"]}}  # Missing 'target_hash'
    successful_count = processor.put_hashtable(hash_info)
    
    if successful_count == 0:
        logger.warning("No hash entries were successfully stored")
        
except ValueError as e:
    logger.error(f"Configuration error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### Validation Example

```python
from rest_client.hash_info_validator import HashInfoValidator

validator = HashInfoValidator()

# Valid hash info
valid_hash_info = {
    "/path/to/file": {
        "target_hash": "abc123",
        "path": "/path/to/file"
    }
}

# Validate
errors = validator.validate(valid_hash_info)
if not errors:
    print("Hash info is valid")
else:
    for error in errors:
        print(f"Validation error: {error}")
```

## Development

### Project Structure

```
rest_client/
├── rest_client/
│   ├── __init__.py                  # Package initialization
│   ├── rest_bootstrap.py            # Main factory class
│   ├── rest_processor.py            # Core REST API processor
│   ├── http_client.py               # HTTP client implementations
│   └── hash_info_validator.py       # Hash info validation
├── configuration/
│   ├── config.py                    # Configuration management
│   └── logging_config.py            # Logging configuration
├── tests/
│   └── test_rest_client.py          # Comprehensive test suite
└── README.md                        # This file
```

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd rest_client

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m unittest discover tests/ -v
```

### Dependencies

- `requests`: HTTP library for making REST API calls
- `typing`: Type hints support (Python 3.5+)

## Testing

The project includes comprehensive unit tests using Python's `unittest` framework.

### Running Tests

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test file
python -m unittest tests.test_rest_client -v

# Run with coverage (if coverage is installed)
coverage run -m unittest discover tests/
coverage report -m
```

### Test Coverage

Tests cover:
- REST API interactions
- HTTP client retry logic
- Hash information validation
- Error handling scenarios
- Configuration management
- Response processing

## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

## Version

Current version: 1.0.0

## Changelog

**v1.0.0 - 2025-01-08**

- Initial release of modularized RestClient package
- **Added:** RestClient factory class for easy instantiation
- **Added:** RestProcessor with comprehensive API interaction methods
- **Added:** RequestsHttpClient with robust retry logic
- **Added:** HashInfoValidator for request validation
- **Added:** Comprehensive error handling and logging
- **Added:** Configuration management with environment variable support
- **Added:** Full type annotations for better development experience

### Roadmap

- [ ] Add support for async/await HTTP operations
- [ ] Implement connection pooling for better performance
- [ ] Add metrics and monitoring capabilities
- [ ] Support for custom authentication methods
- [ ] Add caching layer for frequently accessed data
- [ ] Implement rate limiting features

## Support

- **Issues**: Report bugs and request features by contacting the development team
- **Documentation**: Comprehensive API documentation available in this README
- **Examples**: Multiple usage examples provided in the Examples section

## Acknowledgments

- Built with the `requests` library for HTTP operations
- Comprehensive logging using Python's built-in logging module
- Type annotations for better IDE support and code maintainability
- Modular design for easy testing and extension

---

**Made with 😠 by the SquishyBadger Team**
Feel free to bring us a coffee from the cafeteria!