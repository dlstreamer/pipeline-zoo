FROM ubuntu:18.04

RUN apt update -y \
    && apt install -y libpapi-dev \
       software-properties-common \
       make \
       git \
       cmake \
       pkg-config \
       gcc-4.8-base \
       gcc-4.8 \
       g++-4.8 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-4.8 100 \ 
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-4.8 100  

COPY . /home/system-monitor 

RUN cd /home/system-monitor \
    && mkdir -p _release \
    && cd _release \
    && cmake .. \
    && make 

ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/system-monitor/_release/core_lib:/home/system-monitor

RUN mkdir -p /home/system-monitor/out
WORKDIR /home/system-monitor/out
ENTRYPOINT /home/system-monitor/_release/cmd_client/client 
