# Configuration Module Documentation

## Overview

The Configuration module provides centralized configuration management for REST API applications. It supports loading configuration from environment variables, validates required settings, and provides convenient access methods for common configuration patterns.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Sources](#configuration-sources)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Global Configuration Instance](#global-configuration-instance)

## Quick Start

```python
from squishy_REST_API import config

# Use the default global config instance
database_url = config.get_database_url()
debug_mode = config.is_debug_mode()

# Or create a custom config instance
from squishy_REST_API.configuration.config import Config

custom_config = Config({'debug': True, 'api_port': 8080})
```

## Configuration Sources

The module loads configuration in the following order of precedence (highest to lowest):

1. **Constructor dictionary** - Values passed directly to Config()
2. **Environment variables** - System environment variables
3. **Default values** - Built-in fallback values

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
from squishy_REST_API.configuration.config import Config

# Using environment variables
config = Config()

# Access configuration
print(f"API will run on {config['api_host']}:{config['api_port']}")
print(f"Debug mode: {config.is_debug_mode()}")
```

### Custom Configuration

```python
from squishy_REST_API.configuration.config import Config

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

### Environment Variable Configuration

Set environment variables for automatic configuration:

```bash
export DB_USER="myuser"
export DB_PASSWORD="mypassword"
export SECRET_KEY="mysecretkey"
export DEBUG="true"
export API_PORT="8080"
```

```python
from squishy_REST_API.configuration.config import Config

# Configuration automatically loaded from environment
config = Config()
```

## Error Handling

### ConfigError

Raised when required configuration is missing:

```python
from squishy_REST_API.configuration.config import Config, ConfigError

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

## Global Configuration Instance

A pre-configured global instance is available for convenience:

```python
from squishy_REST_API.configuration.logging_config import logger
from squishy_REST_API import config

# Use the global config instance
database_url = config.get_database_url()

# Use the global logger instance
logger.info("Using global configuration")
```

## Configuration Keys

### Required Keys
- `db_user` - Database username
- `db_password` - Database password
- `secret_key` - Application secret key

### Optional Keys
- `db_type` - Type of database being used (default: mysql)
- `db_host` - Database host (default: localhost)
- `db_port` - Database port (default: 3306)
- `db_name` - Database name (default: mydb)
- `api_host` - API host (default: localhost)
- `api_port` - API port (default: 5000)
- `debug` - Debug mode flag (default: false)
- `log_level` - Logging level (default: INFO)

## Best Practices

1. **Use Environment Variables**: Store sensitive configuration in environment variables rather than hardcoding values
2. **Validate Early**: Create the Config instance early in your application startup to catch configuration errors
3. **Use Global Instance**: For most applications, use the global config instance for consistency
4. **Handle Errors**: Always wrap Config instantiation in try-catch blocks to handle missing configuration gracefully

## Contributing

When adding new configuration options:
1. Add appropriate default values
2. Update the configuration keys documentation
3. Add validation for the new keys
4. Include usage examples