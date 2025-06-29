# Working on dockerfile

## location of squishy work
/mnt/c/Users/joshu/Documents/Current_work/squishy/

## Images
alpine:3.22.0, python:3.12-alpine, mysql:9.3

## Create a container network for rest and DB containers
docker network create --driver bridge DB-net

### To remove
docker network rm DB-net

## Run integrity interactively
```bash
docker run -it --rm \
  --name integrity \
  --network alpine-net \
  -e REST_API_NAME=restapi \
  -e REST_API_PORT=5000 \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/integrity:/squishy \
  alpine:3.22.0 /bin/sh
```
### Install dependencies
```bash
apk add python3 py-yaml py-requests
```

## Run restAPI interactively
```bash
docker run -it --rm \
  --name restapi \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -p 5000:5000 \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_REST_API:/app/squishy_REST_API \
  python:3.12-alpine /bin/sh
```

docker run -d \
  --name squishy-rest-api \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -p 5000:5000 \
  squishy-rest-api:1.0


### Install dependencies
```bash
pip install --no-cache-dir mysql-connector-python PyMySQL sqlalchemy flask gunicorn requests

```
### Attach another instance to the running container
```bash
docker exec -it <container name> /bin/sh
```

### To run in flask
```bash
python3 rest_api.py
```
### To run in gunicorn (multi threaded production server)
```bash
gunicorn -b 0.0.0.0:5000 rest_api:app
```
#TODO need updates to add Nginx reverse proxy


## Run sql container detached
```bash
docker run -d \
  --name mysql-squishy-db \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=squishy_db \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=your_user_password \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/hashtable_init.sql:/docker-entrypoint-initdb.d/hashtable_init.sql \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/logs_init.sql:/docker-entrypoint-initdb.d/logs_init.sql \
  -p 3306:3306 \
  mysql:9.3
```


/mnt/c/Users/joshu/Documents/Current_work/squishy/DB_package
### tests
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/test_hashtable.sql
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < tests/test_hashtable.sql


## integrity.py file structure
empty   # dir with no contents
dir1    # dir with one file, 
    file1   # contents "test_text2"
dir2    # dir with -s link
    lnk1    # link to file1
dir3    # dir with hardlink
    hlnk1   # link to file1
dir4    # dir with dir
    dir4_1
dir5    # dir with all
    dir5_1  # dir with file
        file2   # contents "test_text3"
    lnk2    # link to file2
    hlnk2   # link to file1
    lnk3    # link to dir1

## Commands to create file structure in current directory
```bash
mkdir empty dir1 dir2 dir3 dir4 dir4/dir4_1 dir5 dir5/dir5_1 
echo test_text2 > dir1/file1
echo test_text3 > dir5/dir5_1/file2
ln -s dir1/file1 dir2/lnk1
ln dir1/file1 dir3/hlnk1
ln -s dir5/dir5_1/file2 dir5/lnk2
ln dir1/file1 dir5/hlnk2
ln -s dir1 dir5/lnk3
```  

## Environment variables and other settings

### squishy_db

container name   
--name mysql-squishy-db \

mounts
1. /hashtable_init.sql:/docker-entrypoint-initdb.d/hashtable_init.sql \
2. /logs_init.sql:/docker-entrypoint-initdb.d/logs_init.sql \
3. database-storage:/var/lib/mysql

env vars

  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=squishy_db \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=your_user_password \

```bash
docker run -it --rm \
  --name integrity \
  --network alpine-net \
  -e REST_API_NAME=restapi \
  -e REST_API_PORT=5000 \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/integrity:/squishy \
  alpine:3.22.0 /bin/sh
```
### Install dependencies
```bash
apk add python3 py-yaml py-requests
```

## Run restAPI interactively
```bash
docker run -it --rm \
  --name restapi \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -p 5000:5000 \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_REST_API:/app/squishy_REST_API \
  python:3.12-alpine /bin/sh
```
```bash
docker run -d \
  --name squishy-rest-api \
  --network squishy_db_default \
  -e LOCAL_MYSQL_USER=your_app_user \
  -e LOCAL_MYSQL_PASSWORD=your_user_password \
  -e API_SECRET_KEY=squishy_key_12345 \
  -p 5000:5000 \
  squishy-rest-api:1.0
```

### Install dependencies
```bash
pip install --no-cache-dir mysql-connector-python PyMySQL sqlalchemy flask gunicorn requests

```
### Attach another instance to the running container
```bash
docker exec -it <container name> /bin/sh
```

### To run in flask
```bash
python3 rest_api.py
```
### To run in gunicorn (multi threaded production server)
```bash
gunicorn -b 0.0.0.0:5000 rest_api:app
```
#TODO need updates to add Nginx reverse proxy


## Run sql container detached
```bash
docker run -d \
  --name mysql-squishy-db \
  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=squishy_db \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=your_user_password \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/hashtable_init.sql:/docker-entrypoint-initdb.d/hashtable_init.sql \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/logs_init.sql:/docker-entrypoint-initdb.d/logs_init.sql \
  -p 3306:3306 \
  mysql:9.3
```


/mnt/c/Users/joshu/Documents/Current_work/squishy/DB_package
### tests
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < /mnt/c/Users/joshu/Documents/Current_work/squishy/squishy_db/tests/test_hashtable.sql
docker exec -i mysql-squishy-db mysql -u root -pyour_root_password < tests/test_hashtable.sql


## integrity.py file structure
empty   # dir with no contents
dir1    # dir with one file, 
    file1   # contents "test_text2"
dir2    # dir with -s link
    lnk1    # link to file1
dir3    # dir with hardlink
    hlnk1   # link to file1
dir4    # dir with dir
    dir4_1
dir5    # dir with all
    dir5_1  # dir with file
        file2   # contents "test_text3"
    lnk2    # link to file2
    hlnk2   # link to file1
    lnk3    # link to dir1

## Commands to create file structure in current directory
```bash
mkdir empty dir1 dir2 dir3 dir4 dir4/dir4_1 dir5 dir5/dir5_1 
echo test_text2 > dir1/file1
echo test_text3 > dir5/dir5_1/file2
ln -s dir1/file1 dir2/lnk1
ln dir1/file1 dir3/hlnk1
ln -s dir5/dir5_1/file2 dir5/lnk2
ln dir1/file1 dir5/hlnk2
ln -s dir1 dir5/lnk3
```  

## Environment variables and other settings

### squishy_db

container name   
--name mysql-squishy-db \

mounts
1. /hashtable_init.sql:/docker-entrypoint-initdb.d/hashtable_init.sql \
2. /logs_init.sql:/docker-entrypoint-initdb.d/logs_init.sql \
3. database-storage:/var/lib/mysql

env vars

  -e MYSQL_ROOT_PASSWORD=your_root_password \
  -e MYSQL_DATABASE=squishy_db \
  -e MYSQL_USER=app_user \
  -e MYSQL_PASSWORD=your_user_password \