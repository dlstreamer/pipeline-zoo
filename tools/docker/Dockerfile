# Copyright (c) 2021 Intel Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

ARG BASE=openvino/ubuntu20_data_dev:2021.4.2
ARG REGISTRY
FROM ${REGISTRY}${BASE} as media-analytics-pipeline-zoo
ARG PIPELINE_ZOO_PLATFORM=DEFAULT
ARG GITHUB_TOKEN
ARG PIPELINE_LIST

ENV PIPELINE_ZOO_PLATFORM=$PIPELINE_ZOO_PLATFORM
ENV PIPELINE_ZOO_BASE_IMAGE=${REGISTRY}$BASE
ENV INTEL_OPENVINO_DIR=/opt/intel/openvino

USER root

# Install these below dependencies for OpenVINO base image based pipeline-zoo docker images
RUN if [ -f /opt/intel/openvino/install_dependencies/install_openvino_dependencies.sh ]; then \
       /opt/intel/openvino/install_dependencies/install_openvino_dependencies.sh -y ;\
    fi

RUN if [ -f /opt/intel/openvino/install_dependencies/install_NEO_OCL_driver.sh ]; then \
       /opt/intel/openvino/install_dependencies/install_NEO_OCL_driver.sh -y ; exit 0; \ 
    fi    

RUN if [ -f /opt/intel/openvino/install_dependencies/install_NCS_udev_rules.sh ]; then \
       apt-get install -y -q --no-install-recommends sudo; \ 
       /opt/intel/openvino/install_dependencies/install_NCS_udev_rules.sh -y ;\
    fi    

# Dependencies installed via apt-get
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y -q --no-install-recommends \
    python3-setuptools \
    python3-pip \
    graphviz-dev \
    pciutils \
    dmidecode \
    cmake \
    bash-completion \
    libyaml-cpp-dev \
    nlohmann-json3-dev \
    numactl \
    libjemalloc-dev \
    python3 \
    lsb-release \
    vim && \
    rm -rf /var/lib/apt/lists/*

ENV nlohmann_json_DIR=/usr/lib/cmake
ENV LD_PRELOAD=libjemalloc.so

COPY . /home/pipeline-zoo
RUN if [ ! -z "$PIPELINE_LIST" ]; then \
        /bin/bash /home/pipeline-zoo/tools/docker/assets/install.sh -l "$PIPELINE_LIST" -t "$GITHUB_TOKEN"; \
    else \
        /bin/bash /home/pipeline-zoo/tools/docker/assets/install.sh; \
    fi

# pipebench tools path
ENV PYTHONPATH=$PYTHONPATH:/home/pipeline-zoo/tools/pipebench

# model zoo
ENV OPEN_MODEL_ZOO_ROOT=/opt/intel/openvino/deployment_tools/open_model_zoo

# model proc
ENV DLSTREAMER_MODEL_PROC_ROOT=/opt/intel/openvino/data_processing/dl_streamer/samples/model_proc

# XDG_RUNTIME_DIR
ENV XDG_RUNTIME_DIR=/home/.xdg_runtime_dir

#Open CL Cache
ENV cl_cache_dir=/home/pipeline-zoo/workspace/.cl-cache

# Bash History
ENV HISTFILE=/home/pipeline-zoo/workspace/.bash_history

# work dir
WORKDIR /home/pipeline-zoo/workspace
