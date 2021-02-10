#!/bin/bash -e
#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#

SOURCE_DIR=$(dirname "$(readlink -f "$0")")

if [ -z "$OPEN_MODEL_ZOO_ROOT" ];then
    OPEN_MODEL_ZOO_ROOT=/opt/intel/dldt/open_model_zoo
fi

# Install Dependencies
DEBIAN_FRONTEND=noninteractive apt-get update && \
    xargs -r -a $SOURCE_DIR/packages.txt apt-get install -y -q --no-install-recommends &&
    rm -rf /var/lib/apt/lists/*

export nlohmann_json_DIR=/usr/lib/cmake

# Build omz_demos

mkdir -p omz_demos_build
mkdir -p omz_demos_src/demos
cp -rf $OPEN_MODEL_ZOO_ROOT/demos/common ./omz_demos_src/demos
cp $OPEN_MODEL_ZOO_ROOT/demos/* ./omz_demos_src/demos >/dev/null 2>&1 || true
cp -rf $OPEN_MODEL_ZOO_ROOT/demos/object_detection_demo ./omz_demos_src/demos
cp -rf $OPEN_MODEL_ZOO_ROOT/demos/thirdparty ./omz_demos_src/demos
export HOME=$SOURCE_DIR
./omz_demos_src/demos/build_demos.sh

# Build pipeline runner
rm -rf $SOURCE_DIR/omzrun/build; mkdir -p $SOURCE_DIR/omzrun/build; cd $SOURCE_DIR/omzrun/build; cmake ..; make; cd $SOURCE_DIR
