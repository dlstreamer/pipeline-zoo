#!/bin/bash -e
#
# Copyright (C) 2022 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#
NVIDIA_BASE_IMAGE=nvcr.io/nvidia/deepstream:6.1-devel
SCRIPT=$(realpath "$0")
DOCKERFILE_DIR=$(dirname "$SCRIPT")
TAG=dlstreamer-pipeline-zoo-nvidia:latest

bash ../build.sh --base $NVIDIA_BASE_IMAGE --dockerfile-dir $DOCKERFILE_DIR --tag $TAG 
