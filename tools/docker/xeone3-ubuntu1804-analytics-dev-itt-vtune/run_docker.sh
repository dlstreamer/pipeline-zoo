#!/bin/bash

docker run -it  -v /tmp/.X11-unix/:/tmp/.X11-unix -e DISPLAY=$DISPLAY --cap-add=SYS_ADMIN --cap-add=SYS_PTRACE openvisualcloud/xeone3-ubuntu1804-analytics-dev:itt_vtune /bin/bash
