# SquishyBadger Integrity Service

A containerized microservice that generates cryptographic Merkle tree 
structures from local file systems to enable efficient integrity verification.
The service scans designated file system paths, computes hash-based tree 
representations of directory structures and file contents, then transmits 
the results to a remote storage backend. This approach provides rapid, 
low-overhead detection of inconsistencies, corruption, or unauthorized 
changes between distributed file system copies through mathematical proof 
verification rather than expensive byte-by-byte comparisons.

## Table of Contents

- [Service Operation](#service-operation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
  - [IntegrityCheck](#integrity-check-package-api-documentation)
  - [RestClient](#restclient)
- [Development](#development)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Project Status](#project-status)
- [Version and Change Log](#version)
- [Roadmap](#roadmap)

## Service Operation
The squishy-integrity service requires no local input. Each time the service or container is started
it will: 
1. Use the default config values (or modified env. vars)
2. Collect necessary information from the database (via the REST API) to determine its workload
3. Process portions of the local file tree mounted to the containers `/baseline`
4. Send the computed results to the configured REST API
5. Exit gracefully

## Quick Start
There is a quick start for all the services in the root README.md, if you want to start just the
squishy_integrity service use the instructions below.
### Using Docker (Recommended)

#### Build the Container
```bash
docker build -t squishy-integrity .
```

#### Run with Docker
```bash
docker run -d \
  --name squishy-integrity \
  --network squishy_db_default \
  -v /location/of/baseline:/baseline  \
  squishy-integrity
```

### Example Usage

```bash
# run an interactive session with the `squishy-integrity` container
docker run -it --rm \
  --name squishy-integrity \
  --network squishy_db_default \
  -v /location/of/baseline:/baseline  \
  squishy-integrity
  
# once at the container prompt
python -m squishy_integrity

# squishy_integrity will make requests to the database (through the REST API)
# complile a list of directories and files to run hash checks on, return the 
# results to the database, and exit.
```

## Configuration

### Required Environment Variables
None (defaults configured for typical operation)

### Other configurable Environment Variables
| Variable         | Description                         | Default            |
|------------------|-------------------------------------|--------------------|
| `REST_API_HOST`  | REST API hostname                   | `squishy-rest-api` |
| `REST_API_PORT`  | REST API port                       | `5000`             |
| `BASELINE`       | Internal mount location of baseline | `/baseline`        |
| `DEBUG`          | REST API debugging                  | `False`            |
| `LOG_LEVEL`      | REST API logging level              | `INFO`             | 


### Non-configurable variables
| Variable          | Description                                            | Default |
|-------------------|--------------------------------------------------------|---------|
| `max_retries`     | number of attempts to contact REST API before failure  | `3`     |
| `retry_delay`     | number of seconds between retries                      | `5`     |
| `long_delay`      | Long hold-down during retry attempts                   | `30`    |
| `max_runtime_min` | Minutes to allow integrity check to run                | `10`    |

# API Reference
# Integrity Check Package API Documentation

## Overview

The `integrity_check` package provides a comprehensive solution for file system integrity verification using Merkle trees. It offers modular components for hashing files, walking directory trees, and storing hash information.

## Installation

```python
from integrity_check import IntegrityCheckFactory
```

## Quick Start

```python
# Create a service instance
service = IntegrityCheckFactory.create_service()

# Compute integrity hash for a directory
hash_result = service.compute_merkle_tree("/path/to/root", "/path/to/target")
```

## API Reference

### IntegrityCheckFactory

Main factory class for creating integrity check components.

#### Methods

##### `create_service() -> MerkleTreeService`

Creates a fully configured `MerkleTreeService` with default implementations.

**Returns:**
- `MerkleTreeService`: Configured service instance

**Example:**
```python
from integrity_check import IntegrityCheckFactory

service = IntegrityCheckFactory.create_service()
```

---

### MerkleTreeService

Primary service class for Merkle tree integrity operations.

#### Constructor

```python
MerkleTreeService(
    hash_storage: HashStorageInterface,
    tree_walker: DirectoryTreeWalker,
    file_hasher: FileHasher,
    path_validator: PathValidator
)
```

#### Methods

##### `compute_merkle_tree(root_path: str, dir_path: str) -> Optional[str]`

Computes a Merkle tree hash for a directory and its contents.

**Parameters:**
- `root_path` (str): Root directory of the monitored tree
- `dir_path` (str): Directory to hash (must be within root_path)

**Returns:**
- `Optional[str]`: Directory hash string, or None if computation fails

**Example:**
```python
hash_result = service.compute_merkle_tree("/home/user", "/home/user/documents")
```

##### `remove_redundant_paths_with_priority(priority: list, routine: list) -> list`

Removes redundant paths from provided lists while preserving priority order.

**Parameters:**
- `priority` (list): Paths that should be processed first
- `routine` (list): Paths for routine hash recomputing

**Returns:**
- `list`: Combined, deduplicated list of paths

**Example:**
```python
clean_paths = service.remove_redundant_paths_with_priority(
    priority=["/home/user/important"],
    routine=["/home/user/docs", "/home/user/pics"]
)
```

---

### FileHasher

Handles hashing of files, directories, and symbolic links.

#### Constructor

```python
FileHasher(file_system: FileSystemInterface, hash_function: HashFunction)
```

#### Methods

##### `hash_file(file_path: str) -> str`

Hashes a regular file by reading its contents in chunks.

**Parameters:**
- `file_path` (str): Path to the file to hash

**Returns:**
- `str`: Hexadecimal hash string

##### `hash_link(link_path: str) -> str`

Hashes a symbolic link by its path and target.

**Parameters:**
- `link_path` (str): Path to the symbolic link

**Returns:**
- `str`: Hexadecimal hash string

##### `hash_directory(dir_path: str, hash_info: Dict[str, Any]) -> str`

Hashes a directory based on its contents.

**Parameters:**
- `dir_path` (str): Path to the directory
- `hash_info` (Dict[str, Any]): Hash information for directory contents

**Returns:**
- `str`: Hexadecimal hash string

##### `hash_empty_type(full_path: str, category: str='dirs', return_string: bool=False) -> str`

Provides a standardized way to Hash an empty directory by its path

**Parameters**
- `full_path` (str): Absolute path of the item
- `category` (str): Default `dirs`, other types accepted for modularity
- `return_string` (bool): Default `False` sets the return value to hashable string or hashvalue
 
**Returns**
- `str`: standardized fileHasher directory string, or Hexadecimal hash string of the same.

##### `hash_string(hashable: str) -> str`

Hashes a string using the configured hash function.

**Parameters:**
- `hashable` (str): String to hash

**Returns:**
- `str`: Hexadecimal hash string

---

### DirectoryTreeWalker

Handles directory tree traversal and categorization.

#### Constructor

```python
DirectoryTreeWalker(file_system: FileSystemInterface)
```

#### Methods

##### `get_tree_structure(parent_path: str) -> Dict[str, Dict[str, List[str]]] | bool`

Recursively traverses directory tree and categorizes items.

**Parameters:**
- `parent_path` (str): Root directory path to begin traversal

**Returns:**
- `Dict[str, Dict[str, List[str]]]`: Dictionary mapping paths to their contents
- `bool`: False if parent_path doesn't exist

**Structure of returned dictionary:**
```python
{
    "/path/to/dir": {
        "dirs": ["subdir1", "subdir2"],
        "files": ["file1.txt", "file2.txt"],
        "links": ["symlink1", "symlink2"]
    }
}
```

---

### PathValidator

Validates path operations for integrity checking.

#### Methods

##### `validate_root_and_dir_paths(root_path: str, dir_path: str) -> bool`

Validates that dir_path is within root_path.

**Parameters:**
- `root_path` (str): Root directory path
- `dir_path` (str): Target directory path

**Returns:**
- `bool`: True if dir_path is within root_path

##### `validate_path_exists(path: str) -> bool`

Validates that a path exists.

**Parameters:**
- `path` (str): Path to validate

**Returns:**
- `bool`: True if path exists

---

## Interfaces

### FileSystemInterface

Abstract interface for file system operations.

#### Methods

- `exists(path: str) -> bool`: Check if path exists
- `is_file(path: str) -> bool`: Check if path is a file
- `is_dir(path: str) -> bool`: Check if path is a directory
- `walk(path: str) -> List[Tuple[str | None, list[str] | None, list[str] | None]]`: Walk directory tree
- `read_file_chunks(path: str, chunk_size: int = 65536)`: Read file in chunks
- `readlink(path: str) -> str`: Read symbolic link target

### HashStorageInterface

Abstract interface for hash storage operations.

#### Methods

- `put_hashtable(hash_info: Dict[str, Any]) -> int`: Store hash information
- `get_hashtable(path: str) -> Optional[Dict[str, Any]]`: Retrieve hash table
- `get_single_hash(path: str) -> Optional[str]`: Get single hash value
- `get_oldest_updates(root_path: str, percent: int = 10) -> list[str]`: Get oldest updates
- `get_priority_updates() -> list[str] | None`: Get priority updates
- `get_lifecheck() -> dict | None`: Get the liveness status of REST and DB services
- `put_log() -> int`: Put a log entry in the database

### HashFunction

Abstract interface for hash operations.

#### Methods

- `create_hasher()`: Create hash object
- `hash_string(data: str) -> str`: Hash string data

---

## Implementations

### StandardFileSystem

Standard file system implementation using pathlib.

**Implements:** `FileSystemInterface`

### RestHashStorage

Hash storage implementation using REST connector.

**Implements:** `HashStorageInterface`

**Constructor:**
```python
RestHashStorage(rest_processor)
```

### SHA1HashFunction

SHA-1 hash function implementation.

**Implements:** `HashFunction`

---

## Error Handling

The package includes comprehensive error handling:

- Path validation errors
- File system access errors
- Hash computation failures
- Storage operation failures

All errors are logged using the `squishy_integrity.logger` module.

## Examples

### Basic Usage

```python
from integrity_check import IntegrityCheckFactory

# Create service
service = IntegrityCheckFactory.create_service()

# Compute hash for directory
result = service.compute_merkle_tree("/home/user", "/home/user/documents")
if result:
    print(f"Directory hash: {result}")
else:
    print("Failed to compute hash")
```

### Custom Implementation

```python
from integrity_check.implementations import StandardFileSystem, SHA1HashFunction
from integrity_check.file_hasher import FileHasher

# Create custom file hasher
fs = StandardFileSystem()
hash_func = SHA1HashFunction()
hasher = FileHasher(fs, hash_func)

# Hash a file
file_hash = hasher.hash_file("/path/to/file.txt")
print(f"File hash: {file_hash}")
```

### Path Validation

```python
from integrity_check.validators import PathValidator

validator = PathValidator()

# Validate paths
is_valid = validator.validate_root_and_dir_paths("/home/user", "/home/user/docs")
exists = validator.validate_path_exists("/home/user/docs")
```

### RestClient

Main factory class for creating REST client components.

#### Properties

##### `rest_client -> RestProcessor`

Property that returns a configured `RestProcessor` instance.

**Returns:**
- `RestProcessor`: Configured REST processor instance

**Example:**
```python
from rest_client import RestClient

client = RestClient()
processor = client.rest_client
```

#### Methods

##### `create_rest_connector() -> RestProcessor`

Creates a `RestProcessor` with default HTTP client and validator.

**Returns:**
- `RestProcessor`: Configured REST processor

**Raises:**
- `SystemExit`: If configuration is invalid (exit code 78)

---

### RestProcessor

Core class for REST API interactions and hash storage operations.

#### Constructor

```python
RestProcessor(http_client: HttpClient, validator: HashInfoValidator = None)
```

**Parameters:**
- `http_client` (HttpClient): HTTP client for making requests
- `validator` (HashInfoValidator, optional): Validator for hash information

#### Methods

##### `put_hashtable(hash_info: dict, session_id: str=None) -> int`

    def put_hashtable(self, hash_info: dict, session_id: str=None) -> int:
        """
        Store hash information in the database.

        This method implements the HashStorageInterface.put_hashtable method
        required by the MerkleTreeService.

        Args:
            hash_info: Dictionary containing hash information for files and directories
            session_id: Optional session ID for grouping batches of updates

        Returns:
            int representing the number of updates sent to the REST API that were unsuccessful
        """


Stores hash information in the database via REST API.

**Parameters:**
- `hash_info` (dict): Dictionary containing hash information for files and directories
- `session_id` (int): Optional session ID for grouping batches of updates

**Returns:**
- `int`: Number of unsuccessful updates

**Example:**
```python
hash_info = {
    "/path/to/file": {
        "current_hash": "abc123",
        "dirs": ["subdir1", "subdir2"],
        "files": ["file1.txt", "file2.txt"],
        "links": ["symlink1"]
    }
}
errors = processor.put_hashtable(hash_info)
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

 ##### `get_life_check() -> dict | None`

Retrieves the liveness of the rest api and database.

**Returns:**
- `dict | None`: dict of boolean values with the keys `api` and `db`, or None if an error occurs in processing


##### `put_log() -> int`

Store log information in the database.

**Paremeters:**
- `message` (str): The log message (required)
- `detailed_message` (str): a detailed version of the message
- `log_level` (str): The level of the log entry, defaults to INFO in not provided or an invalid level is specified

---

### HashInfoValidator

Validates hash information data structures.

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
hash_info = {"/path": {"current_hash": "abc123"}}
errors = validator.validate(hash_info)

if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

---

### HttpClient (Abstract Base Class)

Abstract interface for HTTP operations.

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

---

### RequestsHttpClient

Concrete implementation of `HttpClient` using the `requests` library.

#### Constructor

```python
RequestsHttpClient()
```

Initializes with retry configuration from `squishy_integrity.config`.

#### Configuration

Uses the following configuration values:
- `max_retries`: Maximum number of retry attempts
- `retry_delay`: Delay between retries
- `long_delay`: Longer delay between retry cycles

#### Methods

Inherits all methods from `HttpClient` with robust retry logic and error handling.

**Features:**
- Automatic retries with exponential backoff
- Timeout handling (30 seconds default)
- Connection error recovery
- Comprehensive logging

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

## Error Handling

The package provides comprehensive error handling:

### HTTP Status Codes

- **200**: Success
- **404**: Resource not found
- **408**: Request timeout
- **503**: Service unavailable
- **Other codes**: Various HTTP errors

### Exception Handling

- `requests.exceptions.Timeout`: Request timeout
- `requests.exceptions.ConnectionError`: Connection issues  
- `requests.exceptions.RequestException`: General request failures
- `ValueError`: JSON decode errors

### Logging

All operations are logged using `squishy_integrity.logger`:

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
        "current_hash": "required_hash_value",
        "current_dtg_latest": "optional_timestamp",
        "dirs": ["list", "of", "directories"],
        "files": ["list", "of", "files"],
        "links": ["list", "of", "symlinks"]
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

## Configuration

The package uses `squishy_integrity.config` for configuration:

```python
# Required configuration
rest_api_url = "https://api.example.com"

# HTTP client configuration
max_retries = 3
retry_delay = 1.0
long_delay = 5.0
```

---

## Examples

### Complete Workflow

```python
from rest_client import RestClient

# Initialize client
client = RestClient()
processor = client.rest_client

# Prepare hash information
hash_info = {
    "/home/user/documents": {
        "current_hash": "abc123def456",
        "dirs": ["subfolder1", "subfolder2"],
        "files": ["document1.txt", "document2.pdf"],
        "links": ["shortcut1"]
    }
}

# Store hash information
errors = processor.put_hashtable(hash_info)
if errors == 0:
    print("All hashes stored successfully")
else:
    print(f"{errors} hashes failed to store")

# Retrieve hash information
retrieved = processor.get_hashtable("/home/user/documents")
if retrieved:
    print(f"Current hash: {retrieved['current_hash']}")
    print(f"Contains {len(retrieved.get('files', []))} files")

# Get directories needing updates
old_dirs = processor.get_oldest_updates("/home/user", percent=15)
for path in old_dirs:
    print(f"Directory needs update: {path}")
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

# Use custom client
custom_client = CustomHttpClient()
validator = HashInfoValidator()
processor = RestProcessor(custom_client, validator)
```

### Error Handling Example

```python
try:
    hash_info = {"/invalid": {}}  # Missing required 'current_hash'
    errors = processor.put_hashtable(hash_info)
    
    if errors > 0:
        print("Some updates failed - check logs for details")
        
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Development

### Project Structure

```
squishy_integrity/
├── core.py                          # Application entry point
├── integrity_check/
│   ├── file_hasher.py               # Methods for consistent hashes
│   ├── tree_walker.py               # Methods for discovering the file tree
│   ├── validators.py                # Helper class to validate file paths
│   ├── merkle_tree_service.py       # Builds the Merkle tree and updates the DB
│   ├── interfaces.py                # Various abstract class definitions
│   ├── implementations.py           # Concrete implementations of interfaces.py
│   └── app_factory.py               # Integrity application factory
├── rest_client/                 
│   ├── rest_bootstrap.py            # Produces configured RestClient instances
│   ├── http_client.py               # Get and Post methods with robust error handling
│   ├── rest_processor.py            # Connector for interacting with the REST API
│   └── hash_info_validator.py       # Validate hash info formatting before sending to REST
├── configuration/                   # Test suite (not included in container)
│   ├── config.py                    # Main configuration
│   ├── logging_config.py            # System logging configuration
├── tests/                           # Test suite (not included in container)
│   ├── test_merkle_tree_service.py  # Merkle tests
│   └── test_rest_connector.py       # Validate functionallity of connector
├── requirements.txt                 # Python dependencies
└── README.md
```

### Local Development Setup
Start by cloning the repository to your workspace.
```bash
# Clone the repository
git clone <repository-url>
cd squishy-integrity
```
1. **Prerequisites**: Python 3.12+
2. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Database Setup**: The current test suite uses python unittest's `mock` to conduct tests without
database connectivity. Ensure REST API a is running
4. **Environment**: All defaults are set in the configuration module. Environment variables are only
required if you wish to change the [default configuration](#configuration)
5. **Run**: `python -m squishy_integrity`

## Testing

The project includes comprehensive unit and integration tests using Python's `unittest` framework. Tests cover:

- Merkle tree validity
- REST API connection interfaces
- Error handling and edge cases
- Configuration validation

Run tests with detailed output:
```bash
python -m unittest discover squishy_integrity/tests/ -v
```

## Error Handling

### Common Error Messages
- `"Path not found"`: Requested resource doesn't exist
- `"path required but not found in your request json"`: Missing required field
- `"Database error, see DB logs"`: Internal database issue
- `"root_path parameter is required"`: Missing query parameter

## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

## Version

Current version: 1.2.0

## Changelog

**v1.2.0 - 2025-07-03**
-  **Modified:** Merkle process to correct bug that prevented traversing the full height of the tree.

**v1.0.5 - 2025-07-01**

-   **Changed:** Core.py entrypoint to exit on 'suspicious' conditions (like empty baseline)
-   **Removed:** Added 'session_id' fingerprint for tracking and grouping log entries.

**v1.0.0 - 2025-06-26**

-   Baseline of current project state.

### Roadmap
- [ ] Comprehensive logging and monitoring
- [ ] Performance optimization

## Support

- **Issues**: Report bugs and request features by contacting us
- **Documentation**: Less detailed docs available on the [confluence space](http://confluence)

## Acknowledgments

- Containerization with Docker
- Testing framework: Python unittest

---

**Made with 😠 by the SquishyBadger Team**
Feel free to bring us a coffee from the cafeteria!