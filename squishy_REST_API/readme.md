# SquishyBadger REST API

A containerized REST API for SquishyBadger that provides seamless integration between worker applications (such as integrity verification services) and both local and core SquishyBadger databases. Built with Python Flask and designed for production deployment.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Development](#development)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

### Using Docker (Recommended)

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
  -p 5000:5000 \
  squishy-rest-api
```

#### Run with Docker Compose
Create a `docker-compose.yml` file:

```yaml
services:
  squishy-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: squishy-rest-api
    environment:    
      LOCAL_MYSQL_USER: your_app_user
      LOCAL_MYSQL_PASSWORD: your_user_password
      API_SECRET_KEY: squishy_key_12345
    ports:
      - "5000:5000"
    networks:
      - squishy_db_default
  
networks:
  squishy_db_default:
    external: true
```

Then run:
```bash
docker-compose up -d
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
| Variable      | Description     | Default Value |
|---------------|-----------------|-----------|
| `LOCAL_MYSQL_USER`     | MySQL username  | `None` |
| `LOCAL_MYSQL_PASSWORD` | MySQL password  | `None` |
| `API_SECRET_KEY`      | API session key | `None` |

### Other configurable Environment Variables
| Variable               | Description            | Default              |
|------------------------|------------------------|----------------------|
| `LOCAL_DB_TYPE`        | Type of storage to use | `mysql` |
| `LOCAL_MYSQL_HOST`     | MySQL hostname         | `mysql-squishy-db` |
| `LOCAL_MYSQL_DATABASE` | MySQL database name    | `squishy_db`       |
| `LOCAL_MYSQL_PORT`     | MySQL server port      | `3306`               |
| `API_HOST`             | REST API address       | `0.0.0.0`          |
| `API_PORT`             | REST API port          | `5000`               |
| `DEBUG`                | REST API debugging     | `False`              |
| `LOG_LEVEL`            | REST API logging level | `'INFO'`              | 

### Non-configurable variables
| Variable                      | Description                            | Default |
|-------------------------------|----------------------------------------|--------|
| `workers`                     | number of gunicorn workers             | `4`      |
| `worker_class`                | gunicorn request handling              | `sync` |
| `timeout`                     | Time before resetting idle workers     | `30`     |
| `keepalive`                   | Seconds to wait for requests           | `2`      |
| `max_requests`                | Maximum requests before worker reset   | `1000`   |
| `max_requests_jitter`         | jitter tolerance to add to requests    | `100`    |
| `accesslog` | log write to location (default syslog) |  `-`   |
| `errorlog` | log write to location (default errorlog) | `-` |                
| `proc_name` | The name given to the process in the system | `squishy_rest_api` | 
| `use_gunicorn` | Run the application with gunicorn (not dev) | `True` | 


### Connection Details

- **Host**: `localhost` (or container name in Docker networks)
- **Port**: `5000` (configurable via `API_PORT`)
- **Base URL**: `http://localhost:5000/api/`

## API Reference

### Base URL
All endpoints are prefixed with `/api/`

### Response Format
```json
{
    "message": "Success|Error message",
    "data": {} // Response data (when applicable)
}
```

### Endpoints

#### Hash Table Operations

**GET /api/hashtable**
- Retrieve hash record by file path
- Query: File path as query string
- Returns: Complete hash record or 404 if not found

**POST /api/hashtable**
- Insert or update hash record
- Body: `{"path": "string", "hash": "string", "timestamp": "string"}`
- Returns: Operation result with change count

#### Hash Operations

**GET /api/hash**
- Get hash value for specific path
- Query: File path as query string  
- Returns: Hash string or 404 if not found

#### Timestamp Operations

**GET /api/timestamp**
- Get latest timestamp for specific path
- Query: File path as query string
- Returns: Timestamp data or 404 if not found

#### Priority Operations

**GET /api/priority**
- Get prioritized directory list for updates
- Query: `root_path` (required), `percent` (optional, 1-100, default: 10)
- Returns: Ordered list of directories needing updates

#### Health Check

**GET /api/lifecheck**
- Check API and database health status
- Returns: Service health information

### Example Usage

```bash
# Get hash for a file
curl "http://localhost:5000/api/hash?/path/to/file.txt"

# Update hash record
curl -X POST http://localhost:5000/api/hashtable \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/file.txt", "hash": "abc123", "timestamp": "2023-12-01T10:00:00Z"}'

# Get priority directories
curl "http://localhost:5000/api/priority?root_path=/home/user&percent=20"

# Health check
curl http://localhost:5000/api/lifecheck
```

## Development

### Project Structure

```
squishy_REST_API/
├── core.py                      # Application entry point
├── app_factory/
│   ├── api_routes.py            # API endpoint definitions
│   └── app_factory.py           # Flask application factory
├── configuration/               # Application configurations
│   ├── config.py                # Main configuration
│   ├── logging_config.py        # System logging configuration
│   └── database_config.py       # Database implementation config
├── storage_service/             # Database interface implementations
│   ├── local_DB_interface.py    # Abstract interface
│   ├── local_memory.py          # In-memory implementation
│   ├── local_mysql.py           # MySQL implementation
│   └── local_mssql_untested.py  # SQL Server (experimental)
├── tests/                       # Test suite
│   ├── test_api.py              # API endpoint tests
│   └── test_storage_service.py  # Database tests
├── docker-compose.yaml          # Docker compose file
├── Dockerfile                   # Container build instructions
├── requirements.txt             # Python dependencies
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