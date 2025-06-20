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
  --network DB-net \
  -e LOCAL_MYSQL_NAME=local_squishy_db \
  -e LOCAL_USER=squishy \
  -e LOCAL_PASSWORD=squishy \
  -e LOCAL_DATABASE=local_squishy_db \
  -e LOCAL_PORT=5000 \
  -p 80:5000 \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/rest:/squishy \
  python:3.12-alpine /bin/sh
```
### Install dependencies
```bash
apk add py3-flask py3-gunicorn py-requests
pip install --no-cache-dir mysql-connector-python PyMySQL sqlalchemy cryptography flask gunicorn requests

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
  --name local_squishy_db \
  --network DB-net \
  -e MYSQL_USER=squishy \
  -e MYSQL_PASSWORD=squishy \
  -e MYSQL_ROOT_PASSWORD=squishy_root \
  -e MYSQL_DATABASE=local_squishy_db \
  -v /mnt/c/Users/joshu/Documents/Current_work/squishy/DB/init.sql:/docker-entrypoint-initdb.d/init.sql \
  -v sql_volume:/var/lib/mysql \
  -p 3306:3306 \
  mysql:9.3
```

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