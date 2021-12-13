#!/bin/bash -e
#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
SOURCE_DIR=$(dirname "$SCRIPT_DIR")
SOURCE_DIR=$(dirname "$SOURCE_DIR")

PYTEST_PARAMS="$@"
cd ${SOURCE_DIR}; python3 -m pytest -s -v "$PYTEST_PARAMS" --ignore=workspace
