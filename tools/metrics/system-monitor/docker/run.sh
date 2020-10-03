#!/bin/bash
sudo docker run -e http_proxy=$http_proxy -e https_proxy=$http_proxy -v $PWD:/home/system-monitor/out --privileged -it collector:build
