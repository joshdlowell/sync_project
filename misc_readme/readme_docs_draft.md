# Configuration Module Documentation

## Overview

The Configuration module provides centralized configuration management for REST API applications. It supports loading configuration from environment variables, validates required settings, and provides convenient access methods for common configuration patterns.

## Installation

This module is part of the REST API package. No additional installation is required.

## Quick Start

```python
from squishy_REST_API.configuration.config import Config, config

# Use the default global config instance
database_url = config.get_database_url()
debug_mode = config.is_debug_mode()

# Or create a custom config instance
custom_config = Config({'debug': True, 'api_port': 8080})
```

## Configuration Sources

The module loads configuration in the following order of precedence:

1. **Constructor dictionary** (highest priority)
2. **Environment variables**
3. **Default values** (lowest priority)

### Environment Variables

| Config Key | Environment Variable | Default Value | Type |
|------------|---------------------|---------------|------|
| `db_host` | `LOCAL_MYSQL_NAME` | `'mysql-squishy-db'` | string |
| `db_name` | `LOCAL_DATABASE` | `'squishy_db'` | string |
| `db_user` | `LOCAL_USER` | `None` | string |
| `db_password` | `LOCAL_PASSWORD` | `None` | string |
| `db_port` | `LOCAL_MYSQL_PORT` | `3306` | integer |
| `api_host` | `API_HOST` | `'0.0.0.0'` | string |
| `api_port` | `API_PORT` | `5000` | integer |
| `debug` | `DEBUG` | `False` | boolean |
| `secret_key` | `SECRET_KEY` | `None` | string |
| `log_level` | `LOG_LEVEL` | `'INFO'` | string |

### Required Configuration

The following configuration keys are **required** and will raise a `ConfigError` if not provided:

- `db_user`:  The username for the database instance
- `db_password`: The user password for the database instance
- `secret_key`: The session key for HTTP/HTTPS web connections to the rest service

## API Reference

### Classes

#### Config

The main configuration class that manages application settings.

```python
class Config:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None)
```

**Parameters:**
- `config_dict` (dict, optional): Dictionary containing configuration values

**Raises:**
- `ConfigError`: If required configuration keys are missing

#### ConfigError

Custom exception raised for configuration-related errors.

```python
class ConfigError(Exception):
    pass
```

### Methods

#### get()

Retrieve a configuration value by key.

```python
def get(self, key: str, default: Any = None) -> Any
```

**Parameters:**
- `key` (str): Configuration key to retrieve
- `default` (Any, optional): Default value if key not found

**Returns:**
- Configuration value or default

**Example:**
```python
api_port = config.get('api_port', 5000)
custom_setting = config.get('custom_key', 'default_value')
```

#### get_database_url()

Generate a complete database connection URL.

```python
def get_database_url() -> str
```

**Returns:**
- Database connection URL string

**Example:**
```python
db_url = config.get_database_url()
# Returns: "mysql://user:password@host:port/database"
```

#### is_debug_mode()

Check if debug mode is enabled.

```python
def is_debug_mode() -> bool
```

**Returns:**
- `True` if debug mode is enabled, `False` otherwise

**Example:**
```python
if config.is_debug_mode():
    print("Debug mode is active")
```

#### configure_logging()

Set up application logging with configured log level.

```python
def configure_logging(self, logger_name: str = None) -> logging.Logger
```

**Parameters:**
- `logger_name` (str, optional): Name for the logger. Defaults to 'rest_api'

**Returns:**
- Configured logger instance

**Example:**
```python
logger = config.configure_logging('my_api')
logger.info("Application started")
```

### Dictionary-Style Access

The Config class supports dictionary-style access:

```python
# Get values
db_host = config['db_host']

# Check key existence
if 'api_port' in config:
    port = config['api_port']
```

## Usage Examples

### Basic Configuration

```python
from your_package.config import Config

# Using environment variables
config = Config()

# Access configuration
print(f"API will run on {config['api_host']}:{config['api_port']}")
print(f"Debug mode: {config.is_debug_mode()}")
```

### Custom Configuration

```python
from your_package.config import Config

# Override with custom values
custom_config = Config({
    'db_user': 'myuser',
    'db_password': 'mypassword',
    'secret_key': 'mysecretkey',
    'debug': True,
    'api_port': 8080
})

# Use the custom configuration
logger = custom_config.configure_logging()
db_url = custom_config.get_database_url()
```

### Environment Variable Setup

```bash
# Set required environment variables
export LOCAL_USER="api_user"
export LOCAL_PASSWORD="secure_password"
export SECRET_KEY="your-secret-key-here"

# Optional overrides
export DEBUG="true"
export API_PORT="8080"
export LOG_LEVEL="DEBUG"
```

### Database Connection

```python
from your_package.config import config
import sqlalchemy

# Get database URL
db_url = config.get_database_url()

# Create database engine
engine = sqlalchemy.create_engine(db_url)
```

### Logging Setup

```python
from your_package.config import config

# Configure logging
logger = config.configure_logging('my_app')

# Use logger throughout your application
logger.info("Application starting...")
logger.debug("Debug information")
logger.error("An error occurred")
```

## Error Handling

### ConfigError

Raised when required configuration is missing:

```python
from squishy_REST_API import Config, ConfigError

try:
    config = Config({'debug': True})  # Missing required keys
except ConfigError as e:
    print(f"Configuration error: {e}")
    # Output: Configuration error: Missing required configuration keys: db_user, db_password, secret_key
```

### Type Conversion Errors

Raised when environment variables cannot be converted to expected types:

```bash
export LOCAL_MYSQL_PORT="not_a_number"
```

```python
try:
    config = Config()
except ConfigError as e:
    print(f"Invalid configuration: {e}")
    # Output: Invalid configuration: Invalid integer value for db_port: not_a_number
```

## Security Considerations

- Sensitive configuration keys (`db_password`, `secret_key`) are hidden in string representations
- Use environment variables for sensitive data in production
- Never commit sensitive configuration to version control

## Global Configuration Instance

A pre-configured global instance is available for convenience:

```python
from squishy_REST_API import logger
from squishy_REST_API.configuration import config

# Use the global config instance
database_url = config.get_database_url()

# Use the global logger instance
logger.info("Using global configuration")
```

## Changelog

### Version 1.0.0
- Initial release with environment variable support
- Database URL generation
- Logging configuration
- Input validation and type conversion