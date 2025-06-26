# ENV VARS COORDINATION

# Environment Variables
## squishy DB

### required
| Variable | Description | Required | current setting |
|----------|-------------|----------|--|
| `MYSQL_ROOT_PASSWORD` | Root user password | Yes |  your_root_password
| `MYSQL_DATABASE` | Initial database name | Yes | squishy_db
| `MYSQL_USER` | Application user name | Yes | your_app_user
| `MYSQL_PASSWORD` | Application user password | Yes | your_user_password

## squishy rest

| Config Key | Environment Variable   | Default Value                | Type |
|------------|------------------------|------------------------------|------|
| `db_host` | `LOCAL_MYSQL_HOST`     | `'mysql-squishy-db'` | string |
| `db_name` | `LOCAL_MYSQL_DATABASE` | `'squishy_db'`               | string |
| `db_port` | `LOCAL_MYSQL_PORT`     | `3306`                       | integer |
| `api_host` | `API_HOST`             | `'0.0.0.0'`                  | string |
| `api_port` | `API_PORT`             | `5000`                       | integer |
| `debug` | `DEBUG`                | `False`                      | boolean |
| `log_level` | `LOG_LEVEL`            | `'INFO'`                     | string |

### required
| Config Key | Environment Variable   | Default Value | Type |
|------------|------------------------|---------------|------|
| `db_user` | `LOCAL_MYSQL_USER`     | `None` | string |
| `db_password` | `LOCAL_MYSQL_PASSWORD` | `None` | string |
| `secret_key` | `API_SECRET_KEY`       | `None` | string |








# SquishyBadger Containerized REST API

A containerized REST API (Representational State Transfer Application Programming 
Interface) for SquishyBadger based on the Python Flask library. This application 
provides the interface between worker applications (such as the integrity 
verification app) and the local and core SquishyBadger databases.

## Quick Start

### Build from Dockerfile
The included Dockerfile can be used to build the `squishy-rest-api` container 
image locally by running the command below from inside the directory where 
the Dockerfile is located.
```bash
docker build -t squishy-rest-api .
```

### Using Docker Run

TODO - update for gunicorn and dockerbuild ADD CONTAINER NETWORK if interfacing with db container
```bash
docker run -it --rm \
  --name restapi \
  --network DB-net \
  -e LOCAL_MYSQL_NAME=local_squishy_db \
  -e LOCAL_USER=squishy \
  -e LOCAL_PASSWORD=squishy \
  -e LOCAL_DATABASE=local_squishy_db \
  -e LOCAL_PORT=5000 \
  -p 80:5000 \
  -v $(pwd):/squishy_REST_API \
  python:3.12-alpine /bin/sh
```

### Using Docker Compose

Create a `docker-compose.yml` file:
TODO - update for gunicorn and dockerbuild

```yaml
version: '3.8'
services:
  mysql:
    image: python:3.12-alpine
    container_name: restapi
    environment:
      MYSQL_ROOT_PASSWORD: your_root_password
      MYSQL_DATABASE: squishy_db
      MYSQL_USER: app_user
      MYSQL_PASSWORD: your_user_password
    volumes:
      - .:/squishy_REST_API
    ports:
      - "80:5000"
```

Then run:
```bash
docker-compose up -d
```

## Required Files
None: All necessary files are already packaged into the image.

## Environment Variables

TODO ENV VARS FIXING

There are two required environment variables that need to be set at runtime.
They are the Mysql database username `LOCAL_USER` and password 
`LOCAL_PASSWORD`. All other environment variables are pre-set to their default 
values in the image and are sufficient to connect to a default local mssql-squishy-db
instance. 

| Variable | Description                | Required | Default |
|----------|----------------------------|------|---------|
| `LOCAL_USER` | Local Mysql username       | Yes  | None
| `LOCAL_PASSWORD` | Local Mysql user password  | Yes | None
| `LOCAL_MYSQL_NAME` | Local Mysql container name | No | local_squishy_db
| `LOCAL_DATABASE` | Local Mysql database name  | No | local_squishy_db
| `LOCAL_PORT` | REST API port              | No | 5000

## Connection
The REST API will start automatically and can be used via HTTP requests 
(from inside the container network)

- **Host**: localhost (or container name if using Docker network)
- **Port**: 5000

# Detailed docs (AKA Slow Start)
## Project Structure

```
squishy_REST_API/
├── config.py                    # Configuration and logging setup
├── main.py                      # Main entry point
├── app_factory/
│   ├── api_routes.py
│   ├── app_factory.py           # Application factory
│   └── database.py
├── DB_connections/              # Interface and implementations for data storage
│   ├── local_DB_interface.py
│   ├── local_memory.py
│   ├── local_mssql_untested.py
│   └── local_mysql.py
├── tests/                       # Unittests for the squishy_REST_API package
│   ├── readme_tests.md
│   ├── test_api.py
│   └── test_DBconnections.py
└── README.md
```
## Quick Start

```bash
python -m squishy_REST_API.main
```

## API Reference

### Main Module

#### `main()`
This serves as the main entry point for the REST API application.
It creates and runs the REST API application with configuration-based settings.

**Parameters:**
None

**Returns:**
None

**Example:**

```python
from squishy_REST_API.core import main

# Start the application
main()
```

## Dependencies

- Flask
- Custom app factory (`squishy_REST_API.app_factory`)
- Custom configuration system (`squishy_REST_API.config`)

## Usage Examples

### Basic Usage

```python
from squishy_REST_API.core import main

if __name__ == '__main__':
    main()
```

### Custom Configuration

Before running the application, ensure your configuration is properly set:

```python
from squishy_REST_API.configuration.config import config

# Update configuration
config.update({
    'api_host': 'localhost',
    'api_port': 8080,
    'debug': True
})

from squishy_REST_API.core import main

main()
```

### Development

For development purposes, you can run the application in debug mode by setting the `debug` configuration value to `True`.


## REST Interface
### Inputs
This app accepts and processes HTTP GET and POST requests at the REST API 
endpoints available in the squishy_REST_API package's `api_routes.py`.

## Base URL

All API endpoints are prefixed with `/api/`

## Response Format

All API responses follow a consistent JSON format:

```json
{
    "message": "Success|Error message",
    "data": {} // Response data (when applicable)
}
```

## Endpoints

### Hash Table Operations

#### GET /api/hashtable

Retrieve a hash record by file path.

**Parameters:**
- **Query String**: The file path to lookup (passed as raw query string)

**Response:**
- **200 OK**: Hash record found
- **404 Not Found**: Path not found in database

**Example Request:**
```
GET /api/hashtable?/path/to/file.txt
```

**Example Response:**
```json
{
    "message": "Success",
    "data": {
        "path": "/path/to/file.txt",
        "hash": "abc123...",
        "timestamp": "2023-12-01T10:00:00Z"
    }
}
```

#### POST /api/hashtable

Insert or update a hash record.

**Request Body:**
```json
{
    "path": "string (required)",
    "hash": "string (optional)",
    "timestamp": "string (optional)",
    // ... other hash-related fields
}
```

**Response:**
- **200 OK**: Record successfully inserted/updated
- **400 Bad Request**: Missing required 'path' field
- **500 Internal Server Error**: Database operation failed

**Example Request:**
```json
{
    "path": "/path/to/file.txt",
    "hash": "def456...",
    "timestamp": "2023-12-01T10:00:00Z"
}
```

**Example Response:**
```json
{
    "message": "Success",
    "data": {
        "changes": 1,
        "operation": "updated"
    }
}
```

### Single Hash Operations

#### GET /api/hash

Retrieve only the hash value for a specific path.

**Parameters:**
- **Query String**: The file path to lookup

**Response:**
- **200 OK**: Hash value found
- **404 Not Found**: Path not found in database

**Example Request:**
```
GET /api/hash?/path/to/file.txt
```

**Example Response:**
```json
{
    "message": "Success",
    "data": "abc123def456..."
}
```

### Timestamp Operations

#### GET /api/timestamp

Retrieve the latest timestamp for a specific path.

**Parameters:**
- **Query String**: The file path to lookup

**Response:**
- **200 OK**: Timestamp found
- **404 Not Found**: Path not found in database

**Example Request:**
```
GET /api/timestamp?/path/to/file.txt
```

**Example Response:**
```json
{
    "message": "Success",
    "data": {
        "path": "/path/to/file.txt",
        "timestamp": "2023-12-01T10:00:00Z"
    }
}
```

### Priority Operations

#### GET /api/priority

Get a list of directories that need to be updated based on their age (oldest first).

**Query Parameters:**
- **root_path** (required): The root directory to start the search from
- **percent** (optional): Percentage of directories to return (1-100, default: 10)

**Response:**
- **200 OK**: Priority list generated successfully
- **400 Bad Request**: Missing or invalid parameters

**Example Request:**
```
GET /api/priority?root_path=/home/user&percent=20
```

**Example Response:**
```json
{
    "message": "Success",
    "data": [
        {
            "path": "/home/user/old_directory",
            "last_updated": "2023-11-01T08:00:00Z"
        },
        {
            "path": "/home/user/another_old_dir", 
            "last_updated": "2023-11-05T14:30:00Z"
        }
    ]
}
```

### Health Check

#### GET /api/lifecheck

Check the health status of the API and database connection.

**Response:**
- **200 OK**: Service health information

**Example Response:**
```json
{
    "message": "Success",
    "data": {
        "api": true,
        "db": true
    }
}
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **405 Method Not Allowed**: HTTP method not supported for endpoint
- **500 Internal Server Error**: Server error occurred

### Error Response Format

All errors follow the standard response format:

```json
{
    "message": "Descriptive error message"
}
```

**Common Error Messages:**
- `"Path not found"`: Requested path doesn't exist in database
- `"path required but not found in your request json"`: Missing required path field
- `"Database error, see DB logs"`: Internal database operation failed
- `"root_path parameter is required"`: Missing required query parameter
- `"Invalid percent parameter"`: Percent value outside valid range (1-100)

## Rate Limiting

Currently, no rate limiting is implemented.

## Logging

All API requests and responses are logged for debugging and monitoring purposes. Log levels include DEBUG, INFO, WARNING, and ERROR messages.


# Configuration module
This app utilizes a global conifguration module (supporting the factory pattern). A detailed 
README file is included in the `configuration` package.
# Storage service module
This app implements the `storage_service` module. A detailed README file is included 
in the `storage_service` package.
# Unit testing module
The `squishy_REST_API` also includes a suite of unit and integration tests. The tests 
are written using Python's builtin `unittests` library and located in the `/app/squishy_REST_API/tests` directory. A detailed README file is included 
in the `tests` package

## Changelog

### Version 1.0.0
- Initial release with environment variable support
- Database URL generation
- Logging configuration
- Input validation and type conversion

# Readme outline

Project Title: A clear and concise name for your project.
Description: A brief overview of what your project does, its purpose, and key features.
Table of Contents (Optional, but recommended for longer READMEs): Helps users quickly navigate through different sections.
Requirements: List any necessary prerequisites or dependencies for running the project.
Installation Instructions: Clear steps on how to install or set up the project locally.
Usage Examples: Demonstrations or code snippets showing how to use the project.
Contributing: Guidelines for how others can contribute to your project (e.g., submitting bug reports, suggesting features, creating pull requests).
License: Information about the project's license, clarifying how others can use and distribute the code.
Acknowledgments (Optional): Credit to contributors or individuals who have helped with the project.
Project Status (Optional): Indicates the current state of development (e.g., active, on hold, completed).
Visuals (Optional): Screenshots, GIFs, or diagrams to illustrate the project's features or usage.
Support (Optional): Information on where users can find help or support.
Roadmap (Optional): Outlines future plans or releases for the project. 