# Working on dockerfile

## location of squishy work
/mnt/c/Users/joshu/Documents/Current_work/squishy/

## Image
alpine:3.22.0

## Create a container network
docker network create --driver bridge alpine-net

### To remove
docker network rm alpine-net

## Run integrity interactively
docker run -it --rm --name integrity --network alpine-net -v /mnt/c/Users/joshu/Documents/Current_work/squishy:/squishy alpine:3.22.0 /bin/sh
apk add python3 py-yaml py-requests

## Run restAPI interactively
docker run -it --rm --name restapi --network alpine-net -v /mnt/c/Users/joshu/Documents/Current_work/squishy:/squishy alpine:3.22.0 /bin/sh
apk add python3 py3-flask


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

### commands to create file structure in current directory
mkdir empty dir1 dir2 dir3 dir4 dir4/dir4_1 dir5 dir5/dir5_1 
echo test_text2 > dir1/file1
echo test_text3 > dir5/dir5_1/file2
ln -s dir1/file1 dir2/lnk1
ln dir1/file1 dir3/hlnk1
ln -s dir5/dir5_1/file2 dir5/lnk2
ln dir1/file1 dir5/hlnk2
ln -s dir1 dir5/lnk3
  