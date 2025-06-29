# To spin up a full suite

## location of squishy work
/mnt/c/Users/joshu/Documents/Current_work/squishy/

## Base images
python:3.12-alpine, mysql:9.3

## Quick start to bring up using docker
## Create a container network for the pod containers
```bash
docker network create --driver bridge squishy_db_default
```
### To remove
```bash
docker network rm squishy_db_default
```
## Start the containers

### Run sql container detached
#### My local version
```bash
docker run -d \
  --name mysql-squishy-db \
  --network squishy_db_default \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=squishy_db \
  -e MYSQL_USER=your_app_user \
  -e MYSQL_PASSWORD=your_user_password \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/init_scripts:/docker-entrypoint-initdb.d \
  -p 3306:3306 \
  mysql:9.3
```

#### Final version (in db readme)
```bash
docker run -d \
  --name mysql-squishy-db \
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
docker logs mysql-squishy-db
```

#### Run the tests
#### My local version
```bash
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/test_hashtable.sql
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/test_logs.sql
```
#### Final version (in db readme)
```bash
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < squishy_db/tests/test_hashtable.sql
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < squishy_db/tests/test_logs.sql
```

### Run REST API container detached
#### First time through you will need to build the container image
```bash
docker build -t squishy-rest-api:v1.0 . -f Dockerfile_rest
```

You can run this container for testing, or for production
#### Run interactive for testing
This command will start the docker container without launching the rest api service and add the tests 
to the package
```bash
docker run -it --rm \
  --name squishy-rest-api \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/squishy_REST_API/tests:/app/squishy_REST_API/tests \
  -p 5000:5000 \
  squishy-rest-api:v1.0 /bin/sh
```
******With all my local files mounted for development
```bash
docker run -it --rm \
  --name squishy-rest-api \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e LOG_LEVEL=DEBUG \
  -p 5000:5000 \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_REST_API:/app/squishy_REST_API \
  squishy-rest-api:v1.0 /bin/sh
```

Run tests with detailed output:
```bash
python -m unittest discover squishy_REST_API/tests/ -v
```

#### Run the container detached for production
```bash
docker run -d \
  --name squishy-rest-api \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -p 5000:5000 \
  squishy-rest-api:v1.0
```

Check the logs to ensure the service started correctly
```bash
docker logs squishy-rest-api
```

### Run integrity interactively
#### First time through you will need to build the container image
```bash
docker build -t squishy-integrity:v1.0 . -f Dockerfile_integrity
```

You can run this container for testing, or for production. In production the
container will reach out to the db (via the rest_api) and perform a hash of the
files mounted to `/baseline` inside the container
#### Run interactive for testing
This command will start the docker container without launching the integrity service and add the tests 
to the package

```bash
docker run -it --rm \
  --name squishy-integrity \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/squishy_integrity/tests:/app/squishy_integrity/tests \
  squishy-integrity:v1.0 /bin/sh
```
******With all my local files mounted for development
```bash
docker run -it --rm \
  --name squishy-integrity \
  --network squishy_db_default \
    -e LOG_LEVEL=DEBUG \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_integrity:/app/squishy_integrity \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy-integrity:v1.0 /bin/sh
```

Run tests with detailed output:
```bash
python -m unittest discover squishy_integrity/tests/ -v
```

#### Run the container detached for production
```bash
docker run -d \
  --name squishy-integrity \
  --network squishy_db_default \
    -v <location of baseline>:/baseline \
  squishy-integrity:v1.0
```
************** for my testing
```bash
docker run -d \
  --name squishy-integrity \
  --network squishy_db_default \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy-integrity:v1.0
```

Check the logs to ensure the service is running
```bash
docker logs squishy-integrity
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
- [ ] Implement session_id for merkle logging grouping in Rest API
- [ ] Implement putting log entries in DB for merkle status
- [ ] Implement putting log entries in DB for REST API
- [ ] Move string handling (for files dirs links) in responses from rest_processor.py to REST API
- [ ] More comprehensive tests to ensure stability of API during code updates
- [ ] Performance optimization

---

**Made with 😠 by the SquishyBadger Team**













