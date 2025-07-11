# Squishy Integrity

A containerized Python package that orchestrates periodic integrity verification of file systems using Merkle tree cryptographic structures. The service coordinates with external integrity checking components and REST APIs to systematically scan designated file system paths, prioritize processing workloads, and manage execution within configurable time limits.

## Table of Contents

- [Service Operation](#service-operation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
  - [Core Module](#core-module)
  - [Configuration Module](#configuration-module)
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

The squishy-integrity service requires no local input and operates as an orchestration layer. Each time the service or container is started it will:

1. Initialize with default configuration values (or modified environment variables)
2. Create an integrity check service instance via the `IntegrityCheckFactory`
3. Query the database (via REST API) to determine workload priorities and routine updates
4. Process portions of the local file tree mounted to the container's `/baseline` within configured time limits
5. Coordinate the transmission of computed results to the configured REST API
6. Exit gracefully upon completion or timeout

The service acts as a coordinator between the `integrity_check` package (which handles the actual Merkle tree computation) and the storage backend, managing execution flow and resource constraints.

## Quick Start

There is a quick start for all the services in the root README.md. If you want to start just the squishy-integrity service, use the instructions below.

### Using Docker (Recommended)

#### Build the Container
The Dockerfile (and associated `.dockerignore`) is located in the root of the SquishyBadger repo and named `Dockerfile_integrity`

```bash
docker build -t squishy-integrity:v1.2 . -f Dockerfile_integrity
```

#### Run with Docker

```bash
docker run -d \
  --name squishy-integrity \
  --network squishy_db_default \
  -v /location/of/baseline:/baseline  \
  squishy-integrity:v1.2
```

### Example Usage

```bash
# Run an interactive session with the `squishy-integrity` container
docker run -it --rm \
  --name squishy-integrity \
  --network squishy_db_default \
  -v /location/of/baseline:/baseline  \
  squishy-integrity:v1.2
  
# Once at the container prompt
python -m squishy_integrity

# squishy_integrity will coordinate with the integrity_check package to:
# - Make requests to the database (through the REST API)
# - Compile a list of directories and files to run hash checks on
# - Execute integrity checks within time limits
# - Return results to the database, and exit
```

## Configuration

### Required Environment Variables
None (defaults configured for typical operation)

### Configurable Environment Variables

| Variable         | Description                         | Default            |
|------------------|-------------------------------------|--------------------|
| `REST_API_HOST`  | REST API hostname                   | `squishy-rest-api` |
| `REST_API_PORT`  | REST API port                       | `5000`             |
| `BASELINE`       | Internal mount location of baseline | `/baseline`        |
| `DEBUG`          | Enable debug mode                   | `False`            |
| `LOG_LEVEL`      | Application logging level           | `INFO`             |

### Non-configurable Variables

| Variable          | Description                                     | Default |
|-------------------|-------------------------------------------------|---------|
| `max_retries`     | Number of attempts to contact REST API         | `3`     |
| `retry_delay`     | Seconds between retries                         | `5`     |
| `long_delay`      | Extended delay during retry attempts            | `30`    |
| `max_runtime_min` | Maximum minutes to allow integrity check to run | `10`    |

## API Reference

### Core Module

The core module provides the main entry point and orchestration logic for the integrity checking process.

#### Functions

##### `main() -> int`

Main entry point to run a routine integrity check.

**Returns:**
- `int`: Exit code (0 for success, non-zero for failure)

**Example:**
```python
from squishy_integrity.core import main

exit_code = main()
if exit_code == 0:
    print("Integrity check completed successfully")
else:
    print("Integrity check failed")
```

##### `get_paths_to_process(merkle_service) -> List[str]`

Retrieves and deduplicates paths that need processing by combining priority and routine updates.

**Parameters:**
- `merkle_service`: Configured MerkleTreeService instance

**Returns:**
- `List[str]`: Deduplicated list of paths to process

**Example:**
```python
from squishy_integrity.core import get_paths_to_process
from integrity_check import IntegrityCheckFactory

service = IntegrityCheckFactory.create_service()
paths = get_paths_to_process(service)
print(f"Processing {len(paths)} paths")
```

##### `process_paths(merkle_service, paths_list: List[str], max_runtime_min: int) -> Tuple[int, int]`

Processes a list of paths within the specified time limit.

**Parameters:**
- `merkle_service`: Configured MerkleTreeService instance
- `paths_list` (List[str]): List of paths to process
- `max_runtime_min` (int): Maximum runtime in minutes

**Returns:**
- `Tuple[int, int]`: (processed_count, total_count)

**Example:**
```python
from squishy_integrity.core import process_paths
from integrity_check import IntegrityCheckFactory

service = IntegrityCheckFactory.create_service()
paths = ["/baseline/dir1", "/baseline/dir2"]
processed, total = process_paths(service, paths, 10)
print(f"Processed {processed} of {total} paths")
```

##### `performance_monitor(merkle_service, operation_name: str)`

Context manager for monitoring operation performance and logging session information.

**Parameters:**
- `merkle_service`: Configured MerkleTreeService instance
- `operation_name` (str): Name of the operation being monitored

**Example:**
```python
from squishy_integrity.core import performance_monitor
from integrity_check import IntegrityCheckFactory

service = IntegrityCheckFactory.create_service()
with performance_monitor(service, "Test Operation"):
    # Your code here
    pass
```

### Configuration Module

The configuration module provides centralized configuration management with environment variable support.

#### Classes

##### `Config`

Singleton configuration class that manages application settings.

**Properties:**
- `rest_api_url` (str): Complete REST API URL
- `session_id` (str): Unique session identifier for log grouping

**Methods:**

###### `get(key: str, default: Any = None) -> Any`

Retrieves configuration value by key.

**Parameters:**
- `key` (str): Configuration key
- `default` (Any, optional): Default value if key not found

**Returns:**
- `Any`: Configuration value or default

**Example:**
```python
from squishy_integrity import config

max_runtime = config.get('max_runtime_min', 10)
api_url = config.rest_api_url
session = config.session_id
```

###### `is_debug_mode() -> bool`

Checks if debug mode is enabled.

**Returns:**
- `bool`: True if debug mode is enabled

**Example:**
```python
from squishy_integrity import config

if config.is_debug_mode():
    print("Debug mode is enabled")
```

##### `ConfigError`

Custom exception for configuration-related errors.

**Example:**
```python
from squishy_integrity.configuration import ConfigError

try:
    # Configuration operation
    pass
except ConfigError as e:
    print(f"Configuration error: {e}")
```

#### Module-level Objects

##### `config`

Default configuration instance available for import.

**Example:**
```python
from squishy_integrity import config

print(f"REST API URL: {config.rest_api_url}")
print(f"Max runtime: {config.get('max_runtime_min')} minutes")
```

##### `logger`

Configured logger instance for the application.

**Example:**
```python
from squishy_integrity import logger

logger.info("Starting integrity check")
logger.error("An error occurred")
```

## Development

### Project Structure

```
squishy_integrity/
├── core.py                          # Main orchestration logic and entry point
├── configuration/                   # Configuration management
│   ├── config.py                    # Main configuration class
│   └── logging_config.py            # Logging configuration
├── __init__.py                      # Package initialization
├── __main__.py                      # Command-line entry point
├── requirements.txt                 # Python dependencies (currently empty)
└── README.md                        # This file
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
   pip install -r requirements.txt  # Currently empty - uses only built-ins
   ```
3. **Dependencies**: Ensure the `integrity_check` package is available in your Python path
4. **Database Setup**: Ensure REST API is running and accessible
5. **Environment**: All defaults are set in the configuration module. Environment variables are only required if you wish to change the [default configuration](#configuration)
6. **Run**: `python -m squishy_integrity`

### Integration with IntegrityCheck Package

This package depends on the `integrity_check` package for actual Merkle tree computation:

```python
from integrity_check import IntegrityCheckFactory

# The factory creates fully configured services
service = IntegrityCheckFactory.create_service()

# The service provides the interface needed by squishy_integrity
service.compute_merkle_tree(root_path, dir_path)
service.remove_redundant_paths_with_priority(priority, routine)
```

## Testing

The project is designed to work with the `integrity_check` package's comprehensive test suite. For integration testing:

1. Ensure the `integrity_check` package is properly installed and tested
2. Test the configuration module with various environment variable combinations
3. Test the core orchestration logic with mock `IntegrityCheckFactory` instances

Run package tests:
```bash
python -m unittest discover -s . -p "test_*.py" -v
```

## Error Handling

The package provides comprehensive error handling for orchestration scenarios:

### Common Error Conditions

- **Configuration Errors**: Missing or invalid configuration values
- **Service Creation Failures**: Problems creating `IntegrityCheckFactory` instances  
- **Path Processing Errors**: Individual path processing failures (logged but don't stop execution)
- **Time Limit Exceeded**: Graceful handling when `max_runtime_min` is reached
- **REST API Connectivity**: Handled by the underlying `integrity_check` package

### Exit Codes

- **0**: Success - all operations completed successfully
- **1**: Failure - fatal error occurred during execution

### Logging

All operations are logged using the configured logger:

- **INFO**: General status updates, processing progress
- **ERROR**: Path processing failures, fatal errors
- **DEBUG**: Detailed operation information (when debug mode enabled)

## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

## Version

Current version: 1.2.0

## Changelog

**v1.2.0 - 2025-01-03**
- **Added:** Complete orchestration framework for integrity checking
- **Added:** Configuration management with environment variable support
- **Added:** Session-based logging for operation tracking
- **Added:** Time-bounded execution with graceful handling
- **Added:** Priority and routine workload coordination
- **Modified:** Separated orchestration logic from core integrity checking

**v1.0.5 - 2025-07-01**
- **Changed:** Core.py entrypoint to exit on 'suspicious' conditions (like empty baseline)
- **Added:** Session ID fingerprint for tracking and grouping log entries

**v1.0.0 - 2025-06-26**
- Baseline of current project state

### Roadmap

- [ ] Enhanced error recovery mechanisms
- [ ] Performance metrics collection
- [ ] Configuration validation improvements
- [ ] Integration test suite expansion

## Support

- **Issues**: Report bugs and request features by contacting us
- **Documentation**: Less detailed docs available on the [confluence space](http://confluence)

## Acknowledgments

- Built on the `integrity_check` package for core Merkle tree functionality
- Containerization with Docker
- Configuration management with environment variable support
- Session-based logging for operation tracking

---

**Made with 😠 by the SquishyBadger Team**
Feel free to bring us a coffee from the cafeteria!