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

#### Run with Docker Compose
Create a `docker-compose.yml` file:

```yaml
services:
   squishy-integrity:
      build:
         context: .
         dockerfile: ../Dockerfile_integrity
      container_name: squishy-integrity
      networks:
         - squishy_db_default
      volumes:
         - /location/of/baseline:/baseline
      restart: unless-stopped

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
cd squishy-integrity

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REST_API_HOST: squishy-rest-api
export REST_API_PORT: 5000
export BASELINE: "/baseline"
export DEBUG: False
export LOG_LEVEL: INFO

# Run the application
python -m squishy_integrity
```

## Configuration

### Required Environment Variables
None

### Other configurable Environment Variables
| Variable         | Description                         | Default            |
|------------------|-------------------------------------|--------------------|
| `REST_API_HOST`  | REST API hostname                   | `squishy-rest-api` |
| `REST_API_PORT`  | REST API port                       | `5000`             |
| `BASELINE`       | Internal mount location of baseline | `/baseline`        |
| `DEBUG`          | REST API debugging                  | `False`            |
| `LOG_LEVEL`      | REST API logging level              | `'INFO'`           | 


### Non-configurable variables
| Variable          | Description                                            | Default |
|-------------------|--------------------------------------------------------|---------|
| `max_retries`     | number of attempts to contact REST API before failure  | `3`     |
| `retry_delay`     | number of seconds between retries                      | `5`     |
| `long_delay`      | Long hold-down during retry attempts                   | `30`    |
| `max_runtime_min` | Minutes to allow integrity check to run                | `10`    |

## API Reference
The squishy-integrity service requires no local input. It will use the default config values
and information from the database (via the REST API) to determine its workload and send the
computed results to the configured REST API

### Example Usage

```bash
# run and interactive session with the `squishy-integrity` container
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

## Development

### Project Structure

```
squishy_REST_API/
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
│   ├── bootstrap.py                 # Produces configured RestClient instances
│   ├── http_client.py               # Get and Post methods with robust error handling
│   ├── rest_processor.py            # Connector for interacting with the REST API
│   └── info_validator.py            # Validate hash info formatting before sending to REST
├── tests/                           # Test suite
│   ├── test_merkle_tree_service.py  # Merkle tests
│   └── test_rest_connector.py       # Validate functionallity of connector
├── config.py                        # Main configuration
├── logging_config.py                # System logging configuration
├── docker-compose.yaml              # Docker compose file
├── Dockerfile                       # Container build instructions
├── requirements.txt                 # Python dependencies
└── README.md
```

### Local Development Setup

1. **Prerequisites**: Python 3.12+
2. **Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Database Setup**: Ensure REST API is running
4. **Environment**: No required environment variables
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

### Roadmap
- [ ] Comprehensive logging and monitoring
- [ ] Performance optimization

## Support

- **Issues**: Report bugs and request features by contacting us
- **Documentation**: Detailed API docs available in `integrity_check/README.md` and `rest_client/README.md`

## Acknowledgments

- Containerization with Docker
- Testing framework: Python unittest

---

**Made with 😠 by the SquishyBadger Team**