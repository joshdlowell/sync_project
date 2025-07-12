# To spin up a full suite

## location of squishy work
```bash
cd /mnt/c/Users/joshu/Documents/Current_work/squishy
```

## Base images
python:3.12-alpine, mysql:9.3

## Quick start to bring up using docker
### Clone the repo
```bash
git: clone
```
### cd into the directory
```bash
cd squishy
```
## Create a container network for the pod containers
```bash
docker network create --driver bridge squishy_db_default
```
### To remove when finished
```bash
docker network rm squishy_db_default
```
## Start the containers

### Run sql container detached
```bash
docker run -d \
  --name mysql_squishy_db \
  --network squishy_db_default \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=squishy_db \
  -e MYSQL_USER=your_app_user \
  -e MYSQL_PASSWORD=your_user_password \
  -v $(pwd)/squishy_db/init_scripts:/docker-entrypoint-initdb.d \
  -p 3306:3306 \
  mysql:9.3
```

Check the logs to ensure the service started correctly
```bash
docker logs mysql_squishy_db
```

#### Run the tests
Ensure the correct tables are present and functioning as intended
```bash
docker exec -i mysql_squishy_db mysql -u root -pyour_root_password < tests/squishy_db/test_hashtable.sql
docker exec -i mysql_squishy_db mysql -u root -pyour_root_password < tests/squishy_db/test_logs.sql
docker exec -i mysql_squishy_db mysql -u root -pyour_root_password < tests/squishy_db/test_sites_state.sql
```

### Run REST API container
#### First time through you will need to build the container image
```bash
docker build -t squishy_rest_api:v2.0 . -f Dockerfile_rest
```
You can run this container for testing, development or, production

#### Run interactive for testing
This command will start the docker container without launching the rest api service, add the tests 
to the container and enable `DEBUG` (verbose) mode
```bash
docker run -it --rm \
  --name squishy_rest_api \
  --network squishy_db_default \
  -e LOCAL_DB_USER=your_app_user \
  -e LOCAL_DB_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e SITE_NAME=SIT0 \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/tests/squishy_REST_API:/app/tests/squishy_REST_API \
  -v $(pwd)/tests/database_client:/app/tests/database_client \
  -p 5000:5000 \
  squishy_rest_api:v2.0 /bin/sh
```

#### Run interactive for development
This setup uses the mysql implementation for the pipeline database
```bash
docker run -it --rm \
  --name squishy_rest_api \
  --network squishy_db_default \
  -e LOCAL_DB_USER=your_app_user \
  -e LOCAL_DB_PASSWORD=your_user_password \
  -e PIPELINE_DB_USER=your_app_user \
  -e PIPELINE_DB_PASSWORD=your_user_password \
  -e PIPELINE_DB_PORT=3306 \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e LOG_LEVEL=DEBUG \
  -e SITE_NAME=SIT0 \
  -p 5000:5000 \
  -v $(pwd)/squishy_REST_API:/app/squishy_REST_API \
  -v $(pwd)/database_client:/app/database_client \
  -v $(pwd)/tests/squishy_REST_API:/app/tests/squishy_REST_API \
  -v $(pwd)/tests/database_client:/app/tests/database_client \
  squishy_rest_api:v2.0 /bin/sh
```

Run tests with detailed output:
```bash
python -m unittest discover squishy_REST_API/tests/ -v
python -m unittest discover database_client/tests/ -v
```

#### Run detached for production
```bash
docker run -d \
  --name squishy_rest_api \
  --network squishy_db_default \
  -e LOCAL_DB_USER=your_app_user \
  -e LOCAL_DB_PASSWORD=your_user_password \
  -e PIPELINE_DB_USER=your_app_user \
  -e PIPELINE_DB_PASSWORD=your_user_password \
  -e PIPELINE_DB_PORT=3306 \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e SITE_NAME=SIT0 \
  -p 5000:5000 \
  squishy_rest_api:v2.0
```

Check the logs to ensure the service started correctly
```bash
docker logs squishy_rest_api
```

### Run integrity container
#### First time through you will need to build the container image
```bash
docker build -t squishy_integrity:v2.0 . -f Dockerfile_integrity
```

You can run this container for testing, development, or for production. 

When the app is run (automatically on spin-up in production) the 
container will reach out to the db (via the rest_api) and perform a hash of the
files mounted to `/baseline` inside the container

#### Run interactive for testing
This command will start the docker container in `DEBUG` (verbose) mode without 
launching the integrity service and add the tests to the package.
**Note:** There are no files mounted to the `/baseline` directory when launched 
using this command.

```bash
docker run -it --rm \
  --name squishy_integrity \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)tests/squishy_integrity:/app/tests/squishy_integrity \
  -v $(pwd)tests/integrity_check:/app/tests/integrity_check \
  squishy_integrity:v2.0 /bin/sh
```
#### Run interactive for development
**********mine*********
```bash
docker run -it --rm \
  --name squishy_integrity \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/squishy_integrity:/app/squishy_integrity \
  -v $(pwd)/integrity_check:/app/integrity_check \
  -v $(pwd)tests/squishy_integrity:/app/tests/squishy_integrity \
  -v $(pwd)tests/integrity_check:/app/tests/integrity_check \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy_integrity:v2.0 /bin/sh
```

```bash
docker run -it --rm \
  --name squishy_integrity \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/squishy_integrity:/app/squishy_integrity \
  -v $(pwd)/integrity_check:/app/integrity_check \
  -v $(pwd)tests/squishy_integrity:/app/tests/squishy_integrity \
  -v $(pwd)tests/integrity_check:/app/tests/integrity_check \
  -v </put/some/useful/path/here>:/baseline \
  squishy_integrity:v2.0 /bin/sh
```

Run tests with detailed output:
```bash
# For integrity package
python -m unittest discover squishy_integrity/tests/ -v

# For rest_api package
python -m unittest discover rest_client/tests/ -v
```

#### Run the container detached for production
**********mine*********
```bash
docker run -d \
  --name squishy_integrity \
  --network squishy_db_default \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy_integrity:v2.0
```

```bash
docker run -d \
  --name squishy_integrity \
  --network squishy_db_default \
    -v <location of baseline>:/baseline \
  squishy_integrity:v2.0
```

Check the logs to ensure the service is running
```bash
docker logs squishy-integrity
```

### Run Coordinator container
#### First time through you will need to build the container image
```bash
docker build -t squishy_coordinator:v1.0 . -f Dockerfile_coordinator
```
You can run this container for testing, development, or for production

When the app is run (automatically on spin-up in production) the 
container will reach out to the db (via the rest_api) and the core instance
(via the core's rest_api) to do hash comparisons, check for inconsistency in
the database and perform demand hashing on files mounted to `/baseline` 
inside the container.

#### Run interactive for testing
This command will start the docker container without launching the coordinator service, add the tests 
to the packages and enable `DEBUG` (verbose) mode
**********mine*********
```bash
docker run -it --rm \
  --name squishy_coordinator \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -e SITE_NAME=SIT0 \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v $(pwd)/tests/rest_client:/app/tests/rest_client \
  -v $(pwd)/tests/integrity_check:/app/tests/integrity_check \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy_coordinator:v1.0 /bin/sh
```

```bash
docker run -it --rm \
  --name squishy_coordinator \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -e SITE_NAME=SIT0 \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v $(pwd)/tests/rest_client:/app/tests/rest_client \
  -v $(pwd)/tests/integrity_check:/app/tests/integrity_check \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v </put/some/useful/path/here>:/baseline \
  squishy_coordinator:v1.0 /bin/sh
```
#### Run interactive for development
*********mine*********
```bash
docker run -it --rm \
  --name squishy_coordinator \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -e SITE_NAME=SIT0 \
  -v $(pwd)/squishy_coordinator:/app/squishy_coordinator \
  -v $(pwd)/rest_client:/app/rest_client \
  -v $(pwd)/integrity_check:/app/integrity_check \
  -v $(pwd)/squishy_coordinator:/app/squishy_coordinator \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v $(pwd)/tests/rest_client:/app/tests/rest_client \
  -v $(pwd)/tests/integrity_check:/app/tests/integrity_check \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy_coordinator:v1.0 /bin/sh
```

```bash
docker run -it --rm \
  --name squishy_coordinator \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -e SITE_NAME=SIT0 \
  -v $(pwd)/squishy_coordinator:/app/squishy_coordinator \
  -v $(pwd)/rest_client:/app/rest_client \
  -v $(pwd)/integrity_check:/app/integrity_check \
  -v $(pwd)/squishy_coordinator:/app/squishy_coordinator \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v $(pwd)/tests/rest_client:/app/tests/rest_client \
  -v $(pwd)/tests/integrity_check:/app/tests/integrity_check \
  -v $(pwd)/tests/squishy_coordinator:/app/tests/squishy_coordinator \
  -v </put/some/useful/path/here>:/baseline \
  squishy_coordinator:v1.0 /bin/sh
```

Run tests with detailed output:
```bash
python -m unittest discover squishy_REST_API/tests/ -v
python -m unittest discover database_client/tests/ -v
```

#### Run the container detached for production
```bash
docker run -d \
  --name squishy_coordinator \
  --network squishy_db_default \
  -e SITE_NAME=SIT0 \
  -v </put/some/useful/path/here>:/baseline \
  squishy_coordinator:v1.0
```

Check the logs to ensure the service started correctly
```bash
docker logs squishy_coordinator
```

## Quicker start to bring up using docker-compose
This project contains a `docker-compose.yaml` file that consolidates all the Docker commands and Dockerfiles for better 
orchestration. This allows all the services to be started using a single command. Using the `depends_on` command in the
docker compose file ensures services start in the correct order:
   - MySQL starts first
   - REST API starts after MySQL
   - Integrity service starts after REST API
Docker Compose also automatically creates and manages the `squishy_db_default` network to ensure that the services
can communicate with each other.
### Usage:
To start all services:
```bash
docker-compose up -d
```
To stop all services:
```bash
docker-compose down
```
To rebuild and start:
```bash
docker-compose up -d --build
```
To view logs:
```bash
docker-compose logs -f [service-name]
```

## Project Status

🟢 **Active Development** - This project is actively maintained and regularly updated.

### Roadmap
- [ ] Implement controller
- [X] Implement web-gui for viewing db data
- [X] Implement session_id for merkle logging grouping in Rest API
- [X] Implement putting log entries in DB for merkle status
- [ ] Implement putting log entries in DB for REST API
- [X] Move string handling (for files dirs links) in responses from rest_processor.py to REST API
- [ ] More comprehensive tests to ensure stability of API during code updates
- [ ] Performance optimization

---

**Made with 😠 by the SquishyBadger Team**
Feel free to bring us a coffee from the cafeteria!













