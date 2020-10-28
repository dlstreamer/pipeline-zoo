#!/bin/bash -e
#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#

SOURCE_DIR=$(dirname "$(readlink -f "$0")")

echo $SOURCE_DIR

# Install Dependencies
DEBIAN_FRONTEND=noninteractive apt-get update && \
    xargs -r -a $SOURCE_DIR/packages.txt apt-get install -y -q --no-install-recommends &&
    rm -rf /var/lib/apt/lists/*

export nlohmann_json_DIR=/usr/lib/cmake

# Build
rm -rf $SOURCE_DIR/gapirun/build; mkdir -p $SOURCE_DIR/gapirun/build; cd $SOURCE_DIR/gapirun/build; cmake ..; make; cd $SOURCE_DIR
