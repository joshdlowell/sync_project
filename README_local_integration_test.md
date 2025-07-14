# To spin up a test suite with a mock core and remote site
```bash
cd /mnt/c/Users/joshu/Documents/Current_work/squishy
```
### Run core sql container detached
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

##### Creating the pipeline database tables locally (Optional)
Running this script will create the pipeline tables in the local database and prepopulate
them with some test data
```bash
docker exec -i mysql_squishy_db mysql -u root -pyour_root_password < squishy_db/misc_scripts/Create_pipeline_and_populate.sql
```

### Run core REST API container
#### First time through you will need to build the container image
```bash
docker build -t squishy_rest_api:v2.0 . -f Dockerfile_rest
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
  -e CORE_NAME=SIT0 \
  -p 5000:5000 \
  -v $(pwd)/squishy_REST_API:/app/squishy_REST_API \
  -v $(pwd)/database_client:/app/database_client \
  -v $(pwd)/tests/squishy_REST_API_tests:/app/tests/squishy_REST_API_tests \
  -v $(pwd)/tests/database_client_tests:/app/tests/database_client_tests \
  squishy_rest_api:v2.0 /bin/sh
```

### Run core integrity container
#### First time through you will need to build the container image
```bash
docker build -t squishy_integrity:v2.0 . -f Dockerfile_integrity
```

```bash
docker run -it --rm \
  --name squishy_integrity \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -v $(pwd)/squishy_integrity:/app/squishy_integrity \
  -v $(pwd)/integrity_check:/app/integrity_check \
  -v $(pwd)/tests/squishy_integrity_tests:/app/tests/squishy_integrity_tests \
  -v $(pwd)/tests/integrity_check_tests:/app/tests/integrity_check_tests \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy_integrity:v2.0 /bin/sh
```


Check the logs to ensure the service is running
```bash
docker logs squishy-integrity
```

You can manually run an integrity check inside the container by using the command
```bash
python -m squishy_integrity
```

### Run Core Coordinator container
#### First time through you will need to build the container image
```bash
docker build -t squishy_coordinator:v1.0 . -f Dockerfile_coordinator
```

#### Run interactive for development
*********mine*********
```bash
docker run -it --rm \
  --name squishy_coordinator \
  --network squishy_db_default \
  -e LOG_LEVEL=DEBUG \
  -e SITE_NAME=SIT0 \
  -e CORE_NAME=SIT0 \
  -v $(pwd)/squishy_coordinator:/app/squishy_coordinator \
  -v $(pwd)/rest_client:/app/rest_client \
  -v $(pwd)/integrity_check:/app/integrity_check \
  -v $(pwd)/tests/rest_client_tests:/app/tests/rest_client_tests \
  -v $(pwd)/tests/integrity_check_tests:/app/tests/integrity_check_tests \
  -v $(pwd)/tests/squishy_coordinator_tests:/app/tests/squishy_coordinator_tests \
  -v /mnt/c/Users/joshu/Downloads:/baseline \
  squishy_coordinator:v1.0 /bin/sh
```
Check the logs to ensure the service started correctly
```bash
docker logs squishy_coordinator
```


# Spin up a remote site


### Run core REST API container
#### First time through you will need to build the container image
```bash
docker build -t squishy_rest_api:v2.0 . -f Dockerfile_rest
```

#### Run interactive for development
This setup uses the mysql implementation for the pipeline database
```bash
docker run -it --rm \
  --name squishy_rest_api \
  --network squishy_db_default \
  -e LOCAL_DB_HOST=mysql_remote_db \
  -e LOCAL_DB_USER=your_app_user \
  -e LOCAL_DB_PASSWORD=your_user_password \
  -e LOCAL_DB_PORT=3307 \
  -e PIPELINE_DB_USER=your_app_user \
  -e PIPELINE_DB_PASSWORD=your_user_password \
  -e PIPELINE_DB_PORT=3306 \
  -e API_SECRET_KEY=squishy_key_12345 \
  -e LOG_LEVEL=DEBUG \
  -e SITE_NAME=SIT0 \
  -e CORE_NAME=SIT0 \
  -p 5000:5000 \
  -v $(pwd)/squishy_REST_API:/app/squishy_REST_API \
  -v $(pwd)/database_client:/app/database_client \
  -v $(pwd)/tests/squishy_REST_API_tests:/app/tests/squishy_REST_API_tests \
  -v $(pwd)/tests/database_client_tests:/app/tests/database_client_tests \
  squishy_rest_api:v2.0 /bin/sh
```


