#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#
ARG BASE=openvisualcloud/xeon-ubuntu1804-analytics-dev:20.4
FROM ubuntu:18.04 as MODEL_ZOO

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y -q --no-install-recommends \
    ca-certificates \
    wget

RUN sh -c "wget https://github.com/opencv/gst-video-analytics/archive/v1.2.1.tar.gz &&  tar -xzf v1.2.1.tar.gz -C / --strip-components 2 --wildcards "*/samples/model_proc/*""
RUN wget https://github.com/openvinotoolkit/open_model_zoo/archive/2021.1.tar.gz && tar -xzf 2021.1.tar.gz -C /

FROM ${BASE} as media-analytics-pipeline-zoo-bench

USER root

# Dependencies for OpenVINO
RUN if [ -f /opt/intel/openvino/install_dependencies/install_openvino_dependencies.sh ]; then \
       /opt/intel/openvino/install_dependencies/install_openvino_dependencies.sh ;\
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
    python3 && \
    rm -rf /var/lib/apt/lists/*

# bash completion
RUN echo -e "if [ -f /etc/bash_completion ] && ! shopt -oq posix; then \n\
    . /etc/bash_completion \n\
fi\n" >> ~/.bashrc

# pipebench
COPY ./pipebench/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt
RUN ln -s /home/pipeline-zoo/tools/pipebench/pipebench/__main__.py /usr/local/bin/pipebench
ENV PYTHONPATH=$PYTHONPATH:/home/pipeline-zoo/tools/pipebench
# Install bash-completion
RUN echo 'eval "$(shtab --shell=bash pipebench.arguments._get_parser_shtab)"' \
  | tee "$(pkg-config --variable=completionsdir bash-completion)"/pipebench

#RUN shtab  -u > ~/.pipebench.completion.bash
#RUN echo -e "\nsource ~/.pipebench.completion.bash \n" >> ~/.bashrc

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
RUN rm -rf /opt/intel/dldt/open_model_zoo
RUN mkdir -p /opt/intel/dldt
COPY --from=MODEL_ZOO /open_model_zoo-2021.1 /opt/intel/dldt/open_model_zoo

# work dir
WORKDIR /home/pipeline-zoo/workspace