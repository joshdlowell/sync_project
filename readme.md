# Working on dockerfile

## location of squishy work
/mnt/c/Users/joshu/Documents/Current_work/squishy/

## Image
alpine:3.22.0

## Run interactively
docker run -it --rm --net=host -v /mnt/c/Users/joshu/Documents/Current_work/squishy:/squishy alpine:3.22.0 /bin/sh

apk add python3
apk add py-yaml
apk add py-requests

