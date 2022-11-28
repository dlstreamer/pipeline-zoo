FROM nvcr.io/nvidia/deepstream:6.1.1-triton
USER root

# Install python bindings
RUN apt-get update\
    && apt install python3-gi python3-dev python3-gst-1.0 python-gi-dev git python-dev \
    python3 python3-pip python3.8-dev cmake g++ build-essential libglib2.0-dev \
    libglib2.0-dev-bin libgstreamer1.0-dev libtool m4 autoconf automake libgirepository1.0-dev libcairo2-dev -y

RUN cd /opt/nvidia/deepstream/deepstream-6.1/sources/ \
    && git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps
RUN cd /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps \
    && git submodule update --init

# Install GVA python
RUN apt-get install -y apt-transport-https ca-certificates -y\
    && update-ca-certificates

RUN cd /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/3rdparty/gst-python/ \
    && if [ -f ./autogen.sh ]; then \
       ./autogen.sh ;\
    fi \
    && make \
 && make install


RUN cd /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/bindings \
    && mkdir build \
&& cd ./build \
&& cmake .. \
&& make \
&& python3 -m pip install --upgrade pip \
&& pip3 install ./pyds-1.1.4-py3-none*.whl

# install dlstreamer and openvino

RUN apt-get update && apt-get install curl gpg-agent software-properties-common -y \
    && curl -sSL https://repositories.intel.com/graphics/intel-graphics.key | apt-key add - \
    && echo "deb [arch=amd64] https://repositories.intel.com/graphics/ubuntu `. /etc/os-release && echo ${UBUNTU_CODENAME}-legacy` main" | tee /etc/apt/sources.list.d/intel-graphics-legacy.list \
    && curl https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | apt-key add - \
    && echo "deb https://apt.repos.intel.com/openvino/2022 `. /etc/os-release && echo ${UBUNTU_CODENAME}` main" | tee /etc/apt/sources.list.d/intel-openvino-2022.list

# Install Intel® DL Streamer
RUN apt-get update && apt-get install intel-dlstreamer-dev -y

# Install OpenVINO™ toolkit (if not installed)
RUN /opt/intel/dlstreamer/install_dependencies/install_openvino.sh

# Setup OpenVINO™ and Intel® DL Streamer environment
RUN echo "source /opt/intel/openvino_2022/setupvars.sh" >> /root/.bashrc \
    && echo "source /opt/intel/dlstreamer/setupvars.sh" >> /root/.bashrc

ENV GST_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/gstreamer-1.0:/opt/intel/dlstreamer/lib/gstreamer-1.0:/opt/intel/dlstreamer/gstreamer/lib/gstreamer-1.0:

ENTRYPOINT echo $ENTRYPOINT

CMD echo $CMD