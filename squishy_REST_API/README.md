# SquishyBadger REST API

A containerized REST API for SquishyBadger that provides seamless integration between worker applications (such as integrity verification services) and both local and core SquishyBadger databases. Built with Python Flask and designed for production deployment with Gunicorn WSGI server.

## Table of Contents

- [Service Operation](#service-operation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
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

The squishy-REST-API service serves as the central service for accessing and updating the local and core databases. It requires several environment variables (see [Configuration](#configuration)). Once started it will: 

1. Listen for `GET` and `POST` requests at its defined endpoints
2. Process and serve data from the core and local databases
3. Provide web-based GUI interface for core sites
4. Return results from database operations
5. Handle logging and monitoring operations

The service automatically detects if it's running on a core site and enables additional functionality including:
- Web-based dashboard and monitoring interface
- Pipeline integration endpoints
- Multi-site status monitoring
- Advanced logging and analytics

## Quick Start

There is a quick start for all the services in the root README.md. If you want to start just the squishy REST API, use the instructions below.

### Using Docker

#### Build the Container
The Dockerfile (and associated `.dockerignore`) is located in the root of the SquishyBadger repo and named `Dockerfile_rest`

```bash
docker build -t squishy-rest-api:v2.0 . -f Dockerfile_rest
```

#### Run with Docker
```bash
docker run -d \
  --name squishy-rest-api \
  --network squishy_db_default \
  -e LOCAL_DB_USER=your_app_user \
  -e LOCAL_DB_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e SITE_NAME=SIT0 \
  -p 5000:5000 \
  squishy-rest-api:v2.0
```

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd squishy-rest-api

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export LOCAL_DB_TYPE=mysql
export LOCAL_DB_HOST=mysql-squishy-db
export LOCAL_DB_DATABASE=squishy_db
export LOCAL_DB_PORT=3306
export SITE_NAME=SIT0
export API_HOST=0.0.0.0
export API_PORT=5000
export DEBUG=False
export LOG_LEVEL=INFO
export LOCAL_DB_USER=your_app_user
export LOCAL_DB_PASSWORD=your_user_password
export API_SECRET_KEY=squishy_key_12345

# Run the application
python -m squishy_REST_API
```

## Configuration

### Required Environment Variables
| Variable             | Description              | Default Value |
|---------------------|--------------------------|---------------|
| `LOCAL_DB_USER`     | Database username        | `None`        |
| `LOCAL_DB_PASSWORD` | Database password        | `None`        |
| `API_SECRET_KEY`    | API session key          | `None`        |
| `SITE_NAME`         | Site ID of current site  | `None`        |

### Other Configurable Environment Variables
| Variable                | Description               | Default            |
|-------------------------|---------------------------|--------------------|
| `LOCAL_DB_TYPE`         | Type of storage to use    | `mysql`            |
| `LOCAL_DB_HOST`         | Database hostname         | `mysql-squishy-db` |
| `LOCAL_DB_DATABASE`     | Database name             | `squishy_db`       |
| `LOCAL_DB_PORT`         | Database port             | `3306`             |
| `PIPELINE_DB_TYPE`      | Pipeline database type    | `mssql`            |
| `PIPELINE_DB_SERVER`    | Pipeline database server  | `mysql-squishy-db` |
| `PIPELINE_DB_NAME`      | Pipeline database name    | `squishybadger`    |
| `PIPELINE_DB_USER`      | Pipeline database user    | `None`             |
| `PIPELINE_DB_PASSWORD`  | Pipeline database password| `None`             |
| `PIPELINE_DB_PORT`      | Pipeline database port    | `1433`             |
| `API_HOST`              | REST API bind address     | `0.0.0.0`          |
| `API_PORT`              | REST API port             | `5000`             |
| `DEBUG`                 | Enable debug mode         | `False`            |
| `LOG_LEVEL`             | Logging level             | `INFO`             |

### Gunicorn WSGI Configuration
| Variable              | Description                                  | Default            |
|-----------------------|----------------------------------------------|--------------------|
| `workers`             | Number of Gunicorn workers                   | `4`                |
| `worker_class`        | Gunicorn worker class                        | `sync`             |
| `timeout`             | Worker timeout in seconds                    | `30`               |
| `keepalive`           | Keep-alive timeout in seconds                | `2`                |
| `max_requests`        | Maximum requests before worker restart       | `1000`             |
| `max_requests_jitter` | Jitter for max_requests                      | `100`              |
| `proc_name`           | Process name in system                       | `squishy_rest_api` |
| `use_gunicorn`        | Use Gunicorn WSGI server                     | `True`             |

### Connection Details

- **Host**: `localhost` (or container name in Docker networks)
- **Port**: `5000` (configurable via `API_PORT`)
- **Base URL**: `http://localhost:5000/api/`
- **Web GUI**: `http://localhost:5000/` (core sites only)

## API Reference

### Core Endpoints (All Sites)

#### Hash Table Operations

**GET /api/hashtable**
- Retrieve hash records by path
- Query parameters:
  - `path` (required): File/directory path
  - `field` (optional): 'hash', 'timestamp', 'record', 'priority', 'untracked', 'orphaned'

**POST /api/hashtable**
- Insert or update hash records
- Request body: JSON with path and hash data

#### Log Operations

**GET /api/logs**
- Retrieve or manage logs
- Query parameters:
  - `action`: 'consolidate', 'shippable', 'older_than'
  - `days` (for older_than): Number of days

**POST /api/logs**
- Add new log entries
- Request body: JSON with log data

**DELETE /api/logs**
- Remove log entries
- Request body: JSON with log_ids array

#### Health Check

**GET /api/health** (also `/health`, `/api/lifecheck`)
- Check API and database health
- Returns service status and timestamps

### Core Site Endpoints

#### Pipeline Operations (Core Sites Only)

**GET /api/pipeline**
- Retrieve pipeline data
- Query parameters:
  - `action`: 'updates' or 'sites'

**POST /api/pipeline**
- Update pipeline data
- Request body: JSON with action ('hash' or 'site_status')

#### Web GUI Routes (Core Sites Only)

**GET /**
- Main dashboard with system overview

**GET /web/hashtable/<path:file_path>**
- Detailed view of specific hash records

**GET /web/liveness**
- Site liveness monitoring page

**GET /web/logs**
- Log viewing and filtering interface

**GET /web/status**
- Hash synchronization status across sites

### Response Format

All API responses follow a consistent format:

**Success Response:**
```json
{
  "message": "Success",
  "data": <response_data>
}
```

**Error Response:**
```json
{
  "error": "Error Type",
  "message": "Error description",
  "status": <http_status_code>
}
```

### Database Integration

The REST API uses the separate `database_client` package for all database operations. This provides:

- Unified interface across different database types
- Automatic connection management
- Transaction support
- Comprehensive error handling
- Support for both local and core database operations

For detailed database client documentation, see the [database_client package documentation](https://github.com/your-org/database_client).

## Development

### Project Structure

```
squishy_REST_API/
├── core.py                         # Application entry point
├── app_factory/
│   ├── __init__.py                 # Package initialization
│   ├── app_factory.py              # Flask application factory
│   ├── db_client_implementation.py # Database client wrapper
│   └── db_client_interface.py      # Database interface definitions
├── configuration/                  # Application configurations
│   ├── config.py                   # Main configuration management
│   └── logging_config.py           # System logging configuration
├── routes/                         # API and web route definitions
│   ├── main_routes.py              # Route registration logic
│   ├── api_routes.py               # Core API endpoints
│   ├── core_routes.py              # Core site specific endpoints
│   ├── gui_routes.py               # Web GUI endpoints
│   ├── error_handlers.py           # Error handling
│   └── utils.py                    # Utility functions
├── web/                            # Web GUI assets
│   ├── static/                     # CSS, JS, images
│   └── templates/                  # Jinja2 templates
├── tests/                          # Test suite
│   ├── test_api_routes.py          # API endpoint tests
│   ├── test_core_routes.py         # Core site tests
│   └── test_gui_routes.py          # Web GUI tests
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

### Development vs Production

The application automatically detects the runtime environment:

- **Development**: Uses Flask's built-in server when `use_gunicorn=False`
- **Production**: Uses Gunicorn WSGI server with optimized settings
- **Core Site Detection**: Automatically enables web GUI and additional endpoints for core sites

## Testing

The project includes comprehensive unit and integration tests using Python's `unittest` framework. Tests cover:

- API endpoint functionality
- Core site specific operations
- Web GUI route handling
- Database client integration
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
- **503**: Service Unavailable (database connection issues)

### Error Response Types
- **Configuration Error**: Missing or invalid configuration
- **Database Error**: Database connection or query issues
- **Validation Error**: Invalid request parameters
- **Not Found**: Requested resource doesn't exist
- **Server Error**: Internal application errors

### Logging

All operations are logged using a structured logging system:

- **DEBUG**: Detailed request/response information
- **INFO**: Normal operation events
- **WARNING**: Potential issues or deprecated usage
- **ERROR**: Application errors that don't stop execution
- **CRITICAL**: Severe errors that may cause service interruption

## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

## Version

Current version: **2.0.0**

## Changelog

**v2.0.0 - 2025-01-03**

- **Added:** Web-GUI interface for core sites
- **Added:** Core site database interface for specialized operations
- **Added:** Pipeline integration endpoints for core sites
- **Added:** Site liveness and synchronization monitoring
- **Added:** Enhanced logging and dashboard functionality
- **Modified:** Separated database client into independent package
- **Modified:** Improved application factory with core site detection
- **Modified:** Enhanced error handling and response formatting
- **Modified:** Gunicorn WSGI server integration for production deployment

**v1.0.0 - 2025-06-26**

- Initial release with basic API functionality
- Hash table operations
- Basic logging support
- MySQL database integration

## Roadmap

- [ ] Enhanced authentication and authorization
- [ ] Rate limiting implementation
- [ ] Performance optimization and caching
- [ ] Additional database backend support
- [ ] Real-time monitoring and alerting
- [ ] Advanced analytics and reporting
- [ ] API versioning support
- [ ] Comprehensive API documentation endpoint
- [ ] Enhanced web GUI features
- [ ] Mobile-responsive interface improvements

## Support

- **Issues**: Report bugs and request features by contacting the development team
- **Documentation**: Detailed API documentation available through the `/api/docs` endpoint
- **Database Client**: See the separate `database_client` package documentation for database operations

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) web framework
- Production deployment with [Gunicorn](https://gunicorn.org/) WSGI server
- Database connectivity powered by the `database_client` package
- Web interface built with Bootstrap and modern web technologies
- Containerization with Docker
- Testing framework: Python unittest

---

**Made with 😠 by the SquishyBadger Team**  
Feel free to bring us a coffee from the cafeteria!