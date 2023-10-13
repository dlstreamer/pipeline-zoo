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

# For latest agama UMD drivers use ./build.sh --base intel/dlstreamer:2022.1.1-ubuntu20-devel
ARG BASE=intel/dlstreamer:2023.0.0-ubuntu22-gpu682-dpcpp-devel
ARG REGISTRY
FROM ${REGISTRY}${BASE} as media-analytics-pipeline-zoo
ARG PIPELINE_ZOO_PLATFORM=DEFAULT
ARG GITHUB_TOKEN
ARG PIPELINE_LIST
ARG ENTRYPOINT="/bin/bash"
ARG CMD="/bin/bash"

ENV PIPELINE_ZOO_PLATFORM=$PIPELINE_ZOO_PLATFORM
ENV PIPELINE_ZOO_BASE_IMAGE=${REGISTRY}$BASE
ENV INTEL_OPENVINO_DIR=/opt/intel/openvino
ENV ENTRYPOINT=$ENTRYPOINT
ENV CMD=$CMD

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
RUN DEBIAN_FRONTEND=noninteractive apt-get --allow-releaseinfo-change update && \
    apt-get install -y -q --no-install-recommends \
    python3-setuptools \
    python3-pip \
    graphviz-dev \
    pciutils \
    dmidecode \
    ffmpeg \
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

# Install Intel(R) Deep Learning Streamer from SRC
ARG DLSTREAMER_SRC_REPO
ARG DLSTREAMER_SRC_VERSION
ARG GRAPHICS_APT_REPO=https://repositories.intel.com/graphics/
RUN if [ ! -z "$DLSTREAMER_SRC_REPO" ]; then \
    curl ${GRAPHICS_APT_REPO}intel-graphics.key | \
    apt-key add - && \
    apt-add-repository "deb [arch=amd64] ${GRAPHICS_APT_REPO}ubuntu/ focal main" && \
       DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y -q --no-install-recommends git libva-dev python-gi-dev && \
       git clone https://$GITHUB_TOKEN@github.com/$DLSTREAMER_SRC_REPO /home/dlstreamer_src; \
    fi

RUN if [ ! -z "$DLSTREAMER_SRC_VERSION" ]; then \
          cd /home/dlstreamer_src && \
          git checkout $DLSTREAMER_SRC_VERSION; \
    fi

RUN if [ ! -z "$DLSTREAMER_SRC_REPO" ]; then \
       cd /home/dlstreamer_src && \
       git submodule init && \
       git submodule update && \
       python3 -m pip install --no-cache-dir -r requirements.txt && \
#       ./scripts/install_metapublish_dependencies.sh && \
       mkdir build && cd build  \
       && cmake \
	     -DCMAKE_BUILD_TYPE=Release \
    	     -DCMAKE_INSTALL_PREFIX=/opt/intel/dlstreamer \
    	     -DENABLE_PAHO_INSTALLATION=OFF \
    	     -DENABLE_RDKAFKA_INSTALLATION=OFF \
    	     -DENABLE_VAAPI=ON \
	         .. \
       && make -j $(nproc) \
       && make install; \
    fi
ENV GST_PLUGIN_PATH=/home/dlstreamer_src/build/intel64:${GST_PLUGIN_PATH}


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

ENTRYPOINT []

CMD []
