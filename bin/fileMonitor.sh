#!/usr/bin/env bash


# the inotify-tools have to be installed
# sudo yum --enablerepo=epel -y install inotify-tools

while inotifywait -r -e create -e delete /directory/to/watch
do
    echo "TASK TO RUN WHEN FILE IN /directory/to/watch IS CREATED OR DELETED"
done