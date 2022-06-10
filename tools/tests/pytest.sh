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
rm -rf /home/pipeline-zoo/coverage_reports
rm -rf /home/pipeline-zoo/test_workspace
mkdir -p /home/test_workspace/.cl-cache
export PYTHONPYCACHEPREFIX=/home
export cl_cache_dir=/home/test_workspace/.cl-cache
cd ${SOURCE_DIR}; python3 -u -m pytest -s -v "$PYTEST_PARAMS" --ignore=workspace --cov --cov-config=/home/pipeline-zoo/tools/tests/.coveragerc --cov-report=html -o cache_dir=/home/.pytest_cache --benchmark-storage=file:///home/.benchmarks || true
chmod a+rw -R /home/coverage_reports
chmod a+rw -R /home/test_workspace
mv /home/coverage_reports /home/pipeline-zoo
mv /home/test_workspace /home/pipeline-zoo
