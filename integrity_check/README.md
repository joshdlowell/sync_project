# Integrity Check Package

A Python package for file system integrity verification using cryptographic Merkle trees. This package provides modular components for hashing files, walking directory trees, and storing hash information to enable efficient detection of file system changes, corruption, or unauthorized modifications.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
  - [IntegrityCheckFactory](#integritycheckfactory)
  - [MerkleTreeService](#merkletreeservice)
  - [FileHasher](#filehasher)
  - [DirectoryTreeWalker](#directorytreewalker)
  - [PathValidator](#pathvalidator)
  - [Interfaces](#interfaces)
  - [Implementations](#implementations)
- [Package Structure](#package-structure)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Development](#development)
- [Testing](#testing)
- [Version](#version)
- [Change Log](#changelog)
- [Support](#support)

## Overview

The `integrity_check` package generates cryptographic Merkle tree structures from file systems to provide:

- **Efficient integrity verification** through mathematical proof rather than byte-by-byte comparison
- **Modular architecture** with pluggable components for different storage backends and hash functions
- **Comprehensive path validation** to ensure operations stay within designated boundaries
- **Robust error handling** with detailed logging for debugging and monitoring
- **Scalable design** suitable for both small directories and large file system hierarchies

## Installation

```python
from integrity_check import IntegrityCheckFactory
```

## Quick Start

```python
# Create a service instance with default configuration
service = IntegrityCheckFactory.create_service()

# Compute integrity hash for a directory
hash_result = service.compute_merkle_tree("/path/to/directory")

if hash_result:
    print(f"Directory hash: {hash_result}")
else:
    print("Failed to compute hash")
```

## Configuration

The package uses a centralized configuration system with environment variable support.

### Configuration Options

| Variable         | Description                         | Default            |
|------------------|-------------------------------------|--------------------|
| `REST_API_HOST`  | REST API hostname                   | `squishy-rest-api` |
| `REST_API_PORT`  | REST API port                       | `5000`             |
| `BASELINE`       | Root path for integrity checking    | `/baseline`        |
| `DEBUG`          | Enable debug mode                   | `False`            |
| `LOG_LEVEL`      | Logging level                       | `INFO`             |

### Custom Configuration

```python
# Pass configuration to factory
config = {
    'rest_api_host': 'localhost',
    'rest_api_port': 8080,
    'root_path': '/custom/path',
    'debug': True
}

service = IntegrityCheckFactory.create_service(config)
```

## API Reference

### IntegrityCheckFactory

Main factory class for creating integrity check components.

#### Methods

##### `create_service(new_config=None, rest_storage=None) -> MerkleTreeService`

Creates a fully configured `MerkleTreeService` with default implementations.

**Parameters:**
- `new_config` (dict, optional): Configuration overrides
- `rest_storage` (RestHashStorage, optional): Pre-configured RestHashStorage object

**Returns:**
- `MerkleTreeService`: Configured service instance

**Example:**
```python
from integrity_check import IntegrityCheckFactory

# Default configuration
service = IntegrityCheckFactory.create_service()

# Custom configuration
custom_config = {'debug': True, 'log_level': 'DEBUG'}
service = IntegrityCheckFactory.create_service(new_config=custom_config)

# Pre-configured RestHashStorage object
from rest_client import RestClient
from integrity_check.implementations import RestHashStorage
rest_client = RestClient().create_rest_connector("http://some_rest_api:8080")
rest_storage = RestHashStorage(rest_client)
service = IntegrityCheckFactory.create_service(rest_storage=rest_storage)
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

##### `compute_merkle_tree(dir_path: str) -> Optional[str]`

Computes a Merkle tree hash for a directory and its contents.

**Parameters:**
- `dir_path` (str): Directory to hash (must be within configured root_path)

**Returns:**
- `Optional[str]`: Directory hash string, or None if computation fails

**Example:**
```python
hash_result = service.compute_merkle_tree("/home/user/documents")
if hash_result:
    print(f"Directory hash: {hash_result}")
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

##### `put_log_w_session(message: str, detailed_message: str=None, log_level: str=None) -> int`

Logs a message with the current session ID.

**Parameters:**
- `message` (str): Log message
- `detailed_message` (str, optional): Detailed log message
- `log_level` (str, optional): Log message level, INFO if omitted

**Returns:**
- `int`: Number of entries successfully added

---

### FileHasher

Handles hashing of files, directories, and symbolic links.

#### Constructor

```python
FileHasher(file_system: FileSystemInterface, hash_function: HashFunction)
```

#### Methods

##### `hash_file(file_path: str) -> str`

Hashes a regular file by reading its contents in chunks, or a special file
by creating a unique identifier.

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

##### `hash_special_file(self, file_path: str) -> str`

Hashes a special file (socket, FIFO, device file, etc.) by its metadata.

**Parameters:**
- `file_path` (str): Path to the file to hash

**Returns:**
- `str`: Hexadecimal hash string

##### `hash_directory(hash_info: Dict[str, Any]) -> str | None`

Hashes a directory based on its contents.

**Parameters:**
- `hash_info` (Dict[str, Any]): Hash information for directory contents

**Returns:**
- `str | None`: Hexadecimal hash string, or None if failed

##### `hash_empty_type(full_path: str, category: str='dirs', return_string: bool=False) -> str`

Provides a standardized way to hash an empty directory by its path.

**Parameters:**
- `full_path` (str): Absolute path of the item
- `category` (str): Default `'dirs'`, other types accepted for modularity
- `return_string` (bool): Default `False`, returns hashable string if True

**Returns:**
- `str`: Standardized hash string or hexadecimal hash value

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
        "links": ["symlink1", "symlink2"],
        "special": ["FIFO1", "Socket2"]
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
- `is_link(self, path: str) -> bool`: Check if path is a symbolic link
- `is_readable_file(self, path: str) -> bool`: Check if path is a readable regular file
- `get_file_metadata(self, path: str) -> Dict[str, Any]`: Get file metadata including type, mode, size, etc.

### HashStorageInterface

Abstract interface for hash storage operations.

#### Methods

- `put_hashtable(hash_info: Dict[str, Any]) -> int`: Store hash information
- `get_hashtable(path: str) -> Optional[Dict[str, Any]]`: Retrieve hash table
- `get_single_hash(path: str) -> Optional[str]`: Get single hash value
- `get_oldest_updates(percent: int = 10) -> list[str]`: Get oldest updates
- `get_priority_updates() -> list[str] | None`: Get priority updates
- `get_health() -> dict | None`: Get service health status
- `put_log(message: str, detailed_message: str=None, log_level: str=None, session_id: str=None) -> int`: Store log entry

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

**Features:**
- Cross-platform path handling
- Robust error handling for file operations
- Efficient file reading with chunked I/O

### RestHashStorage

Hash storage implementation using REST connector.

**Implements:** `HashStorageInterface`

**Constructor:**
```python
RestHashStorage(rest_processor)
```

**Features:**
- RESTful API integration
- Automatic retry logic
- Session-based logging

### SHA256HashFunction

SHA-256 hash function implementation.

**Implements:** `HashFunction`

**Features:**
- Consistent hash computation
- Memory-efficient streaming for large files
- Standard cryptographic implementation

### SHA1HashFunction

SHA-1 hash function implementation.

**Implements:** `HashFunction`

**Features:**
- Consistent hash computation
- Memory-efficient streaming for large files
- Standard cryptographic implementation

---

## Package Structure

```
integrity_check/
├── __init__.py             # Package initialization
├── app_factory.py          # Application factory
├── configuration/
│   ├── config.py           # Main configuration
│   └── logging_config.py   # Logging configuration
├── file_hasher.py          # File hashing methods
├── implementations.py      # Concrete implementations
├── interfaces.py           # Abstract interfaces
├── merkle_tree_service.py  # Main service class
├── tree_walker.py          # Directory traversal
└── validators.py           # Path validation
```

## Error Handling

The package includes comprehensive error handling:

### Common Error Types

- **Path validation errors**: Invalid or inaccessible paths
- **File system access errors**: Permission or I/O issues
- **Hash computation failures**: Corrupted files or system errors
- **Storage operation failures**: Network or database issues
- **Configuration errors**: Invalid or missing configuration

### Error Logging

All errors are logged locally using the configured logging system:
Some (more significant errors) are also stored in the database for issue awareness

- **DEBUG**: Detailed operation information
- **INFO**: General status updates
- **WARNING**: Recoverable errors and retries
- **ERROR**: Operation failures
- **CRITICAL**: System-level failures

### Exception Handling

```python
try:
    hash_result = service.compute_merkle_tree("/path/to/directory")
    if hash_result:
        print(f"Success: {hash_result}")
    else:
        print("Hash computation failed - check logs")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Examples

### Basic Usage

```python
from integrity_check import IntegrityCheckFactory

# Create service with default configuration
service = IntegrityCheckFactory.create_service()

# Compute hash for directory
result = service.compute_merkle_tree("/home/user/documents")
if result:
    print(f"Directory hash: {result}")
else:
    print("Failed to compute hash")
```

### Custom Configuration

```python
# Custom configuration
custom_config = {'debug': True, 'log_level': 'DEBUG'}
service = IntegrityCheckFactory.create_service(new_config=custom_config)

# Pre-configured RestHashStorage object
from rest_client import RestClient
from integrity_check.implementations import RestHashStorage
rest_client = RestClient().create_rest_connector("http://some_rest_api:8080")
rest_storage = RestHashStorage(rest_client)
service = IntegrityCheckFactory.create_service(rest_storage=rest_storage)
```

### Custom Implementation

```python
from integrity_check.implementations import StandardFileSystem, SHA256HashFunction
from integrity_check.file_hasher import FileHasher

# Create custom file hasher
fs = StandardFileSystem()
hash_func = SHA256HashFunction()
hasher = FileHasher(fs, hash_func)

# Hash individual files
file_hash = hasher.hash_file("/path/to/file.txt")
print(f"File hash: {file_hash}")

# Hash symbolic links
link_hash = hasher.hash_link("/path/to/symlink")
print(f"Link hash: {link_hash}")
```

### Path Validation

```python
from integrity_check.validators import PathValidator

validator = PathValidator()

# Validate paths
is_valid = validator.validate_root_and_dir_paths("/home/user", "/home/user/docs")
exists = validator.validate_path_exists("/home/user/docs")

print(f"Path is valid: {is_valid}")
print(f"Path exists: {exists}")
```

### Directory Tree Walking

```python
from integrity_check.implementations import StandardFileSystem
from integrity_check.tree_walker import DirectoryTreeWalker

# Create tree walker
fs = StandardFileSystem()
walker = DirectoryTreeWalker(fs)

# Get directory structure
tree_structure = walker.get_tree_structure("/home/user/documents")
if tree_structure:
    for path, contents in tree_structure.items():
        print(f"Directory: {path}")
        print(f"  Subdirs: {contents['dirs']}")
        print(f"  Files: {contents['files']}")
        print(f"  Links: {contents['links']}")
```

### Path Redundancy Management

```python
# Remove redundant paths while preserving priority
priority_paths = ["/home/user/important", "/home/user/critical"]
routine_paths = ["/home/user/docs", "/home/user/pics", "/home/user/docs/archive"]

clean_paths = service.remove_redundant_paths_with_priority(
    priority=priority_paths,
    routine=routine_paths
)

print(f"Optimized path list: {clean_paths}")
```

## Development

### Prerequisites

- Python 3.12+
- REST API backend (for hash storage)
- Access to file system paths for integrity checking

### Local Development Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**: Set required environment variables or use defaults

3. **Configuration**: Customize configuration as needed for your environment

### Testing

Run the package's test suite:

```bash
python -m unittest discover tests/ -v
```

### Contributing

1. Follow the established interfaces when adding new implementations
2. Add comprehensive tests for new functionality
3. Update documentation for API changes
4. Maintain backward compatibility where possible

## Testing

The package includes comprehensive unit tests covering:

- Merkle tree computation accuracy
- Path validation and security
- File system operations
- Hash function consistency
- Error handling and edge cases
- Configuration validation

### Test Structure

```bash
tests/
└── test_merkle_tree_service.py
```

### Running Tests

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test module
python -m unittest tests.test_merkle_tree_service -v

# Run with coverage
python -m coverage run -m unittest discover integrity_check/tests/
python -m coverage report
```

## Version

Current version: 2.1.0

### Changelog

**v2.1.0**
- Added handling for special files, i.e. socket, FIFO

**v1.2.0**
- Refactored into standalone package
- Added comprehensive API documentation
- Improved error handling and logging
- Added configuration validation
- Enhanced path redundancy management

**v1.0.5**
- Added session ID tracking for log grouping
- Improved error reporting

**v1.0.0**
- Initial release with basic Merkle tree functionality

### Roadmap

- [ ] Improved database logging for better issue awareness
- [ ] Parallel processing for large directory trees
- [ ] File system monitoring integration
- [ ] Performance optimization for large files

## Support

- **Documentation**: Complete API reference and examples provided
- **Issues**: Report bugs and request features by contacting the development team
- **Logging**: Comprehensive logging available for debugging

---

**Made with 😠 by the SquishyBadger Team**  
Feel free to bring us a coffee from the cafeteria!