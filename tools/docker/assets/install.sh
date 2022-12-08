#!/bin/bash -e
#
# Copyright (C) 2019 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Invoke this script only from a Dockerfile
# this will setup the docker image to execute pipeline-zoo
# Invoke ./assets/install.sh -m 
# To pre-download pipelines 
# Invoke <Github token> ./install.sh OR 
# ./install.sh -t <Github token> 

PIPELINE_LIST=""
while getopts "l:ht:" arg; do
  case ${arg} in
    l)
      PIPELINE_LIST=${OPTARG}
      ;;
    t)
      GITHUB_TOKEN=${OPTARG} 
      ;;      
    h)
      echo "$0 usage: "
      echo "-l to specify .yml file containing list of pipelines to download"
      echo "-t to specify the GITHUB_TOKEN"
      exit 0
      ;;
  esac
done

PIPELINE_ZOO_HOME_DIR=/home/pipeline-zoo

# Intel(R) Media Analytics Containers

if [ -d "/opt/intel/samples" ]; then
    PYTHONUSERBASE="/opt/intel/samples"
fi

# Intel(R) Deep Learning Streamer Base Image

GVA_PYTHON_PATH=`PYTHONUSERBASE=$PYTHONUSERBASE python3 -c "import gstgva.video_frame; print(gstgva.video_frame.__file__)"`
if ( [ ! -z $GVA_PYTHON_PATH ] && [ -f $GVA_PYTHON_PATH ] ); then
  cp $PIPELINE_ZOO_HOME_DIR/tools/docker/assets/video_frame.py $GVA_PYTHON_PATH
fi

# OpenVINO(TM) toolkit Base Image 

GVA_PYTHON_PATH=/opt/intel/openvino/data_processing/dl_streamer/python/gstgva/video_frame.py
if [ -f $GVA_PYTHON_PATH ]; then 
    cp $PIPELINE_ZOO_HOME_DIR/tools/docker/assets/video_frame.py $GVA_PYTHON_PATH
fi

# Opt out for telemetry model downloading and converting
TELEMETRY_OPT_IN_OUT=`PYTHONUSERBASE=$PYTHONUSERBASE python3 -c "import openvino_telemetry,os;print(os.path.split(openvino_telemetry.__file__)[0])"`
if ( [ ! -z $TELEMETRY_OPT_IN_OUT ] && [ -d $TELEMETRY_OPT_IN_OUT ] ); then
    PYTHONUSERBASE=$PYTHONUSERBASE python3 $TELEMETRY_OPT_IN_OUT/opt_in_out.py --opt_out
fi

# pip install pipebench tools 
if [ -d $PIPELINE_ZOO_HOME_DIR/tools/pipebench ]; then
  pip3 install  --no-cache-dir -r $PIPELINE_ZOO_HOME_DIR/tools/pipebench/requirements.txt && \
  rm -f $PIPELINE_ZOO_HOME_DIR/tools/pipebench/requirements.txt;
fi
if [ -d $PIPELINE_ZOO_HOME_DIR/tools/downloader ]; then
  pip3 install  --no-cache-dir -r $PIPELINE_ZOO_HOME_DIR/tools/downloader/requirements.txt && \
  rm -f $PIPELINE_ZOO_HOME_DIR/tools/downloader/requirements.txt ;
fi
if [ -d $PIPELINE_ZOO_HOME_DIR/tools/systeminfo ]; then
  pip3 install  --no-cache-dir -r $PIPELINE_ZOO_HOME_DIR/tools/systeminfo/requirements.txt && \
  rm -f $PIPELINE_ZOO_HOME_DIR/tools/systeminfo/requirements.txt ;
fi
if [ -d $PIPELINE_ZOO_HOME_DIR/tools/uploader ]; then
  pip3 install  --no-cache-dir -r $PIPELINE_ZOO_HOME_DIR/tools/uploader/requirements.txt && \
  rm -f $PIPELINE_ZOO_HOME_DIR/tools/uploader/requirements.txt ;
fi
if [ -d $PIPELINE_ZOO_HOME_DIR/tools/tests ]; then
  pip3 install  --no-cache-dir -r $PIPELINE_ZOO_HOME_DIR/tools/tests/requirements.txt && \
  rm -f $PIPELINE_ZOO_HOME_DIR/tools/tests/requirements.txt;
fi

if [ ! -L /usr/local/bin/pipebench ]; then \
  ln -s $PIPELINE_ZOO_HOME_DIR/tools/pipebench/pipebench/__main__.py /usr/local/bin/pipebench; \
fi

export PYTHONPATH=$PYTHONPATH:$PIPELINE_ZOO_HOME_DIR/tools/pipebench

# bash completion
printf "if [ -f /etc/bash_completion ] && ! shopt -oq posix; then \n\
    . /etc/bash_completion \n\
fi\n" >> ~/.bashrc

# Install bash-completion
printf 'eval "$(shtab --shell=bash pipebench.arguments._get_parser_shtab)"' \
  | tee "$(pkg-config --variable=completionsdir bash-completion)"/pipebench

# XDG_RUNTIME_DIR
mkdir -p /home/.xdg_runtime_dir
export XDG_RUNTIME_DIR=/home/.xdg_runtime_dir

#Open CL Cache
mkdir -p $SOURCE_DIR/workspace/.cl-cache
export cl_cache_dir=$PIPELINE_ZOO_HOME_DIR/workspace/.cl-cache

# run pipebench download
if [ ! -z $PIPELINE_LIST ]; then \
  mkdir -p $PIPELINE_ZOO_HOME_DIR/workspace \
  && cd $PIPELINE_ZOO_HOME_DIR/workspace \
  && while read pipeline_name; \
     do pipeline_name=$(echo $pipeline_name | cut -f2 -d' '); \
        GITHUB_TOKEN=$GITHUB_TOKEN PYTHONUSERBASE=$PYTHONUSERBASE pipebench download $pipeline_name; \
        done < $PIPELINE_ZOO_HOME_DIR/$PIPELINE_LIST
fi

