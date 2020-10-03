#!/bin/bash
sudo docker build --build-arg http_proxy=$http_proxy  --build-arg https_proxy=$http_proxy -f docker/Dockerfile --tag collector:build .
