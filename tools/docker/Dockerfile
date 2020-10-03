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

RUN sh -c "wget https://github.com/opencv/gst-video-analytics/archive/v1.1.0.tar.gz &&  tar -xzf v1.1.0.tar.gz -C / --strip-components 2 --wildcards "*/samples/model_proc/*""
RUN wget https://github.com/openvinotoolkit/open_model_zoo/archive/2020.4.tar.gz && tar -xzf 2020.4.tar.gz -C /
RUN ls /
FROM ${BASE} as media-analytics-pipeline-zoo-bench

# Dependencies installed via apt-get
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y -q --no-install-recommends \
    python3-setuptools \
    python3-pip \
    graphviz-dev \
    pciutils \
    dmidecode \
    python3 && \
    rm -rf /var/lib/apt/lists/*


# pipebench
COPY ./pipebench/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

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
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# tests
COPY ./tests/requirements.txt /
RUN pip3 install  --no-cache-dir -r /requirements.txt
RUN rm -f /requirements.txt

# Patches
COPY ./docker/patches/ /

# model proc
RUN mkdir -p /opt/intel/dl_streamer/samples/model_proc
COPY --from=MODEL_ZOO /model_proc /opt/intel/dl_streamer/samples/model_proc

# model zoo
RUN rm -rf /opt/intel/dldt/open_model_zoo
RUN mkdir -p /opt/intel/dldt
COPY --from=MODEL_ZOO /open_model_zoo-2020.4 /opt/intel/dldt/open_model_zoo


# work dir

WORKDIR /home/tools/pipebench