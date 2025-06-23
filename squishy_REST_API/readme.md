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
  --name integrity \
  --network alpine-net \
  -e REST_API_NAME=restapi \
  -e REST_API_PORT=5000 \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/integrity:/squishy \
  alpine:3.22.0 /bin/sh
```

### Using Docker Compose

Create a `docker-compose.yml` file:
TODO - update for gunicorn and dockerbuild

```yaml
version: '3.8'
services:
  mysql:
    image: mysql:9.3
    container_name: mysql-squishy-db
    environment:
      MYSQL_ROOT_PASSWORD: your_root_password
      MYSQL_DATABASE: squishy_db
      MYSQL_USER: app_user
      MYSQL_PASSWORD: your_user_password
    volumes:
      - ./hashtable_init.sql:/docker-entrypoint-initdb.d/hashtable_init.sql
      - ./logs_init.sql:/docker-entrypoint-initdb.d/logs_init.sql
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

volumes:
  mysql_data:
```

Then run:
```bash
docker-compose up -d
```

## Required Files
None: All necessary files are already packaged into the image.

## Environment Variables

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


## Interface
### Inputs
This container accepts and processes HTTP GET and POST requests at these endpoints:

TODO FROM HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

as input enforces the DB schema(s) it is initialized with

`hashtable`: 
1. Minimum required values are `path` and `current_hash`.
2. For new rows, `current_dtg_latest` and `current_dtg_first` are set to the current
time automatically.
3. A column `hashed_path` is generated automatically to enforce uniqueness and act as
primary key (Uniqueness can't be enforced directly on the path column because it is a TEXT column with no defined length limit).

`logs`:
1. Minimum required values are `summary_message`
2. `site_id` must be five or fewer characters, and is set to `local` by default
3. `log_level` is `INFO` by default. If this value is included in an insert or update 
operation it must be one of `ERROR`, `STATUS`, `WARNING`, or `INFO`


## Unit testing
This package also includes unit and integration tests. The tests are written using Python's builtin `unittests` library and
located in the `/app/squishy_REST_API/tests` directory. 

```
python -m squishy_REST_API.tests.test_api
```

swhich can be used to verify that the 
tables exist and are configured in compliance with the Database interface. The scripts use 
transactions that get rolled back at the end, so they won't leave test data in your table.

To run the scripts in your MySQL 9.3 container:

1. **Copy the scripts to your container**:
      ```bash
      docker cp tests/. mysql-squishy-db:/tmp/
      ```
2. **Execute the scripts in the container**:
   ```bash
   docker exec -it mysql-squishy-db mysql -u root -pyour_root_password -e "source /tmp/test_hashtable.sql"
   ```
   ```bash
   docker exec -it mysql-squishy-db mysql -u root -pyour_root_password -e "source /tmp/test_logs.sql"
   ```

Or run them directly:
```bash
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < tests/test_hashtable.sql
```
```bash
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < tests/test_logs.sql
```

### **What the test_hashtable.sql script tests:**

1. **Basic inserts** - Tests simple minimum record insertion
2. **Generated column** - Verifies the hash unique key generation works correctly
3. **Default values** - Verifies default values are applied
4. **Timestamp functionality** - Verifies automatic timestamp generation
5. **Insert all fields** - Verifies that record insertion with all fields works correctly
6. **Update operations** - Tests record updates
7. **Ordered update operations** - Verifies 'in database' field shift then update operations work correctly
8. **Complex queries** - Tests aggregation functions
9. **Data integrity** - Verifies field lengths and constraints
10. **Special characters** - Tests handling of special characters in text fields
11. **Case in-sensitivity** - Verifies current_hash, target_hash, and prev_hash are case-insensitive
12. **Required field enforcement** - Verifies records without required fields are rejected.


### **What the test_logs.sql script tests:**

1. **Basic inserts** - Tests simple record insertion.
2. **Auto increment log_id** - Verifies that log_id auto increments.
3. **Required field enforcement** - Verifies records without required fields are rejected.
4. **Default values** - Verifies default values are applied.
5. **Length enforcement** Verifies length constraints are enforced.
6. **ENUM permitted** Verifies 'log_levels' in the table's list are accepted.
7. **ENUM enforcement** Verifies 'log_levels' must be from table's list.
8. **Full field insertion** - Tests full record insertion.
9. **Case in-sensitivity** - Verifies site_id and log_level are case-insensitive.
