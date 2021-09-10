#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#
ARG BASE=openvino/ubuntu20_data_dev:2021.3_vaapi_fix
ARG PIPELINE_ZOO_PLATFORM=DEFAULT
FROM ubuntu:18.04 as MODEL_ZOO
ARG MODEL_PROC_VERSION=v1.4.1
ARG MODEL_ZOO_VERSION=2021.3

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y -q --no-install-recommends \
    ca-certificates \
    wget 

RUN sh -c "wget https://github.com/opencv/gst-video-analytics/archive/${MODEL_PROC_VERSION}.tar.gz &&  tar -xzf ${MODEL_PROC_VERSION}.tar.gz -C / --strip-components 2 --wildcards "*/samples/model_proc/*""
RUN wget --no-proxy https://gitlab.devtools.intel.com/media-analytics-pipeline-zoo/models/-/archive/main/models-main.tar.gz && mkdir -p /media-analytics-pipeline-zoo/models && tar -xzf models-main.tar.gz -C /media-analytics-pipeline-zoo/models --strip-components 1 --wildcards "*/model-descriptions/*" 
RUN wget https://github.com/openvinotoolkit/open_model_zoo/archive/refs/tags/${MODEL_ZOO_VERSION}.tar.gz && \
    tar -xzf ${MODEL_ZOO_VERSION}.tar.gz -C /media-analytics-pipeline-zoo/ && \
    mv /media-analytics-pipeline-zoo/open_model_zoo-${MODEL_ZOO_VERSION} /media-analytics-pipeline-zoo/open_model_zoo 

FROM ${BASE} as media-analytics-pipeline-zoo
ARG BASE=intel-media-analytics:latest
ARG PIPELINE_ZOO_PLATFORM=ATS

ENV PIPELINE_ZOO_PLATFORM=$PIPELINE_ZOO_PLATFORM
ENV PIPELINE_ZOO_BASE_IMAGE=$BASE
# the base docker image rearranges the directory structure
ENV INTEL_OPENVINO_DIR=/opt/intel/openvino

USER root

# Dependencies installed via apt-get
RUN DEBIAN_FRONTEND=noninteractive && no_proxy=intel.com  &&apt-get update && \
    apt-get install -y -q --no-install-recommends \
    build-essential \ 
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
    python3 && \
    rm -rf /var/lib/apt/lists/*

ENV nlohmann_json_DIR=/usr/lib/cmake
ENV LD_PRELOAD=libjemalloc.so

# bash completion
RUN printf "if [ -f /etc/bash_completion ] && ! shopt -oq posix; then \n\
    . /etc/bash_completion \n\
fi\n" >> ~/.bashrc

# set up GSE image for PL zoo
RUN if [ -d /opt/intel/solutions/dldt/deployment_tools/model-optimizer ]; then \
       mkdir -p /opt/intel/openvino/deployment_tools/ \
       && mv /opt/intel/solutions/dldt/deployment_tools/model-optimizer /opt/intel/openvino/deployment_tools/model_optimizer \
       && cd /opt/intel/openvino/deployment_tools/model_optimizer \
       && python3 -m pip install --upgrade pip \
       && python3 -m pip install -r requirements.txt; \
    fi

# pipebench
COPY ./tools/pipebench/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt
RUN ln -s /home/pipeline-zoo/tools/pipebench/pipebench/__main__.py /usr/local/bin/pipebench
ENV PYTHONPATH=$PYTHONPATH:/opt/intel/solutions/lib/python3.8/site-packages:/home/pipeline-zoo/tools/pipebench
ENV OpenCV_DIR=/opt/intel/solutions/lib/cmake/opencv4
ENV InferenceEngine_DIR=/opt/intel/solutions/dldt/inference_engine/share
ENV ngraph_DIR=/opt/intel/solutions/dldt/deployment_tools/ngraph/cmake

# Install bash-completion
RUN printf 'eval "$(shtab --shell=bash pipebench.arguments._get_parser_shtab)"' \
  | tee "$(pkg-config --variable=completionsdir bash-completion)"/pipebench

# systeminfo
COPY ./tools/systeminfo/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# uploader
COPY ./tools/uploader/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# downloader
COPY ./tools/downloader/requirements.txt /
RUN pip3 install  --no-cache-dir -r/requirements.txt
RUN rm -f /requirements.txt

# tests
COPY ./tools/tests/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# Patches
#COPY ./docker/patches/video_frame.py /opt/intel/openvino/data_processing/dl_streamer/python/gstgva/video_frame.py
COPY ./tools/docker/patches/video_frame.py /opt/intel/solutions/lib/python3.8/site-packages/gstgva/video_frame.py

# model proc
RUN mkdir -p /opt/intel/dl_streamer/samples/model_proc
COPY --from=MODEL_ZOO /model_proc /opt/intel/dl_streamer/samples/model_proc

# model zoo
COPY --from=MODEL_ZOO //media-analytics-pipeline-zoo/open_model_zoo/tools /opt/intel/openvino/deployment_tools/open_model_zoo/tools
COPY --from=MODEL_ZOO //media-analytics-pipeline-zoo/open_model_zoo/models /opt/intel/openvino/deployment_tools/open_model_zoo/models
COPY --from=MODEL_ZOO //media-analytics-pipeline-zoo/open_model_zoo/demos /opt/intel/openvino/deployment_tools/open_model_zoo/demos
ENV OPEN_MODEL_ZOO_ROOT=/opt/intel/openvino/deployment_tools/open_model_zoo

# pipeline zoo models
COPY --from=MODEL_ZOO /media-analytics-pipeline-zoo/models /opt/intel/openvino/deployment_tools/open_model_zoo/models/media-analytics-pipeline-zoo/models

COPY ./tools/downloader /home/pipeline-zoo/tools/downloader/
COPY ./tools/uploader /home/pipeline-zoo/tools/uploader/
COPY ./tools/pipebench /home/pipeline-zoo/tools/pipebench/
COPY ./tools/systeminfo /home/pipeline-zoo/tools/systeminfo/
COPY ./pipelines /home/pipeline-zoo/pipelines
COPY ./runners /home/pipeline-zoo/runners

#Open CL Cache
RUN mkdir -p $SOURCE_DIR/workspace/.cl-cache
ENV cl_cache_dir=/home/pipeline-zoo/workspace/.cl-cache

# XDG_RUNTIME_DIR
RUN mkdir -p /home/.xdg_runtime_dir
ENV XDG_RUNTIME_DIR=/home/.xdg_runtime_dir

# run pipebench download
RUN mkdir /home/pipeline-zoo/workspace \
 && cd /home/pipeline-zoo/workspace \
 && pipebench download od-h265-mbnetssd-v1-coco \
 && pipebench download od-h264-mbnetssd-v1-coco \
 && pipebench download oc-h264-full_frame-resnet_v1.5_50 \
 && pipebench download oc-h265-full_frame-resnet_v1.5_50 \
 && pipebench download oc-h264-mbnetssd-v1-coco-resnet_v1.5_50 \
 && pipebench download oc-h265-mbnetssd-v1-coco-resnet_v1.5_50;

# Bash History
ENV HISTFILE=/home/pipeline-zoo/workspace/.bash_history

WORKDIR /home/pipeline-zoo/workspace

ENTRYPOINT ["/usr/bin/demo-bash"]
