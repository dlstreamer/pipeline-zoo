#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#
ARG BASE=openvino/ubuntu20_data_dev:2021.4.1
ARG PIPELINE_ZOO_PLATFORM=DEFAULT
ARG REGISTRY=
FROM ${REGISTRY}ubuntu:18.04 as MODEL_ZOO
ARG MODEL_PROC_VERSION=v1.4.1

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y -q --no-install-recommends \
    ca-certificates \
    wget

RUN sh -c "wget https://github.com/opencv/gst-video-analytics/archive/${MODEL_PROC_VERSION}.tar.gz &&  tar -xzf ${MODEL_PROC_VERSION}.tar.gz -C / --strip-components 2 --wildcards "*/samples/model_proc/*""
RUN wget --no-proxy https://gitlab.devtools.intel.com/media-analytics-pipeline-zoo/models/-/archive/main/models-main.tar.gz && mkdir -p /media-analytics-pipeline-zoo/models && tar -xzf models-main.tar.gz -C /media-analytics-pipeline-zoo/models --strip-components 1 --wildcards "*/model-descriptions/*" 

FROM ${REGISTRY}${BASE} as media-analytics-pipeline-zoo
ARG BASE=openvino/ubuntu20_data_dev:2021.3_vaapi_fix
ARG PIPELINE_ZOO_PLATFORM=DEFAULT

ENV PIPELINE_ZOO_PLATFORM=$PIPELINE_ZOO_PLATFORM
ENV PIPELINE_ZOO_BASE_IMAGE=${REGISTRY}$BASE
ENV INTEL_OPENVINO_DIR=/opt/intel/openvino

USER root

# Dependencies for OpenVINO
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

# bash completion
RUN printf "if [ -f /etc/bash_completion ] && ! shopt -oq posix; then \n\
    . /etc/bash_completion \n\
fi\n" >> ~/.bashrc

# pipebench
COPY ./pipebench/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt
RUN ln -s /home/pipeline-zoo/tools/pipebench/pipebench/__main__.py /usr/local/bin/pipebench
ENV PYTHONPATH=$PYTHONPATH:/home/pipeline-zoo/tools/pipebench
# Install bash-completion
RUN printf 'eval "$(shtab --shell=bash pipebench.arguments._get_parser_shtab)"' \
  | tee "$(pkg-config --variable=completionsdir bash-completion)"/pipebench

# systeminfo
COPY ./systeminfo/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# uploader
COPY ./uploader/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# downloader
COPY ./downloader/requirements.txt /
RUN pip3 install  --no-cache-dir -r/requirements.txt
RUN rm -f /requirements.txt

# tests
COPY ./tests/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# Patches
COPY ./docker/patches/video_frame.py /opt/intel/openvino/data_processing/dl_streamer/python/gstgva/video_frame.py

# model proc
RUN mkdir -p /opt/intel/dl_streamer/samples/model_proc
COPY --from=MODEL_ZOO /model_proc /opt/intel/dl_streamer/samples/model_proc

# model zoo
# RUN rm -rf /opt/intel/dldt/open_model_zoo
# RUN mkdir -p /opt/intel/dldt
# COPY --from=MODEL_ZOO /open_model_zoo /opt/intel/dldt/open_model_zoo
ENV OPEN_MODEL_ZOO_ROOT=/opt/intel/openvino/deployment_tools/open_model_zoo

# pipeline zoo models
COPY --from=MODEL_ZOO /media-analytics-pipeline-zoo/models /opt/intel/openvino/deployment_tools/open_model_zoo/models/media-analytics-pipeline-zoo/models

# XDG_RUNTIME_DIR
RUN mkdir -p /home/.xdg_runtime_dir
ENV XDG_RUNTIME_DIR=/home/.xdg_runtime_dir

#Open CL Cache
RUN mkdir -p $SOURCE_DIR/workspace/.cl-cache
ENV cl_cache_dir=/home/pipeline-zoo/workspace/.cl-cache

# Bash History

ENV HISTFILE=/home/pipeline-zoo/workspace/.bash_history

# work dir
WORKDIR /home/pipeline-zoo/workspace
