#!/bin/bash -e
#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#
TAG=
RUN_PREFIX=

# Platforms
declare -A PLATFORMS=(["DEFAULT"]=1 ["ATS"]=3)
PLATFORM=DEFAULT

# Base Images
DEFAULT_BASE_IMAGE=openvino/ubuntu20_data_dev:2021.4.2
ATS_BASE_IMAGE=intel-media-analytics:latest

# Model Proc Versions
ATS_MODEL_PROC_VERSION=v1.3 
DEFAULT_MODEL_PROC_VERSION=v1.4.1

DOCKERFILE_DIR=$(dirname "$(readlink -f "$0")")
DOCKERFILE=${DOCKERFILE_DIR}/Dockerfile
SOURCE_DIR=$(dirname $DOCKERFILE_DIR)
BUILD_ARGS=$(env | cut -f1 -d= | grep -E '_(proxy|REPO|VER)$' | sed 's/^/--build-arg / ' | tr '\n' ' ')
BUILD_OPTIONS="--network=host"

NO_CACHE=
REGISTRY=

get_options() {
    while :; do
        case $1 in
        -h | -\? | --help)
            show_help
            exit
            ;;
	--platform)
            if [ "$2" ]; then
                PLATFORM=$2
                shift
            else
                error 'ERROR: "--platform" requires an argument.'
            fi
            ;;
        --base)
            if [ "$2" ]; then
                BASE_IMAGE=$2
                shift
            else
                error 'ERROR: "--base" requires an argument.'
            fi
            ;;
	--model-proc-version)
            if [ "$2" ]; then
                MODEL_PROC_VERSION=$2
                shift
            else
                error 'ERROR: "--model_proc_version" requires an argument.'
            fi
            ;;
        --build-arg)
            if [ "$2" ]; then
                BUILD_ARGS+="--build-arg $2 "
                shift
            else
                error 'ERROR: "--build-arg" requires an argument.'
            fi
            ;;
        --tag)
            if [ "$2" ]; then
                TAG=$2
                shift
            else
                error 'ERROR: "--tag" requires an argument.'
            fi
            ;;
	--registry)
	    if [ "$2" ]; then
		REGISTRY=$2
		shift
	    else
		error 'ERROR: "--docker-image-cache" requires an argument.'
	    fi
	    ;;
        --dockerfile-dir)
            if [ "$2" ]; then
                DOCKERFILE_DIR=$2
                shift
            else
                error 'ERROR: "--dockerfile-dir" requires an argument.'
            fi
            ;;
        --dry-run)
            RUN_PREFIX="echo"
            echo ""
            echo "=============================="
            echo "DRY RUN: COMMANDS PRINTED ONLY"
            echo "=============================="
            echo ""
            ;;
	--no-cache)
	    NO_CACHE=" --no-cache"
            ;;
        --)
            shift
            break
            ;;
         -?*)
	    error 'ERROR: Unknown option: ' $1
            ;;
	 ?*)
	    error 'ERROR: Unknown option: ' $1
            ;;
        *)
            break
            ;;
        esac

        shift
    done

    if [ ! -z "$PLATFORM" ]; then
	PLATFORM=${PLATFORM^^}
	if [[ ! -n "${PLATFORMS[$PLATFORM]}" ]]; then
	    error 'ERROR: Unknown platform: ' $PLATFORM
	fi
	PLATFORM_PREFIX=${PLATFORM//-/_}
	if [ -z "$BASE_IMAGE" ]; then
	    BASE_IMAGE=${PLATFORM_PREFIX}_BASE_IMAGE
	    BASE_IMAGE=${!BASE_IMAGE}
	fi
	if [ -z "$MODEL_PROC_VERSION" ]; then
	    MODEL_PROC_VERSION=${PLATFORM_PREFIX}_MODEL_PROC_VERSION
	    MODEL_PROC_VERSION=${!MODEL_PROC_VERSION}
	fi
    fi

    if [ -z "$TAG" ]; then
        TAG="media-analytics-pipeline-zoo"
	if [ ! -z "$PLATFORM" ] && [ $PLATFORM != 'DEFAULT' ]; then
	    TAG+="-${PLATFORM,,}"
	fi
    fi
    
}


show_image_options() {
    echo ""
    echo "Building Media Analytics Pipeline Zoo Image: '${TAG}'"
    echo ""
    echo "   Base: '${BASE_IMAGE}'"
    echo "   Build Context: '${SOURCE_DIR}'"
    echo "   Dockerfile: '${DOCKERFILE_DIR}/Dockerfile'"
    echo "   Build Options: '${BUILD_OPTIONS}'"
    echo "   Build Arguments: '${BUILD_ARGS}'"
    echo "   Platform: '${PLATFORM}'"
    echo ""
}

show_help() {
    echo "usage: build.sh"
    echo "  [--base base image]"
    echo "  [--platform platform one of ${!PLATFORMS[@]}]"
    echo "  [--build-arg additional build args to pass to docker build]"
    echo "  [--tag tag for image]"
    echo "  [--dockerfile-dir specify a different dockerfile directory]"
    echo "  [--dry-run print docker commands without running]"
    exit 0
}

error() {
    printf '%s %s\n' "$1" "$2" >&2
    exit 1
}

get_options "$@"

if [ $PLATFORM = "ATS" ]; then
    DOCKERFILE="$DOCKERFILE_DIR/intel-media-analytics/Dockerfile"
    SOURCE_DIR=$(builtin cd $DOCKERFILE_DIR; cd ../../; pwd)
fi

# BUILD IMAGE

BUILD_ARGS+=" --build-arg REGISTRY=$REGISTRY "
BUILD_ARGS+=" --build-arg BASE=$BASE_IMAGE "
BUILD_ARGS+=" --build-arg MODEL_PROC_VERSION=$MODEL_PROC_VERSION "
BUILD_ARGS+=" --build-arg PIPELINE_ZOO_PLATFORM=$PLATFORM "

show_image_options

if [ -z "$RUN_PREFIX" ]; then
    set -x
fi

$RUN_PREFIX docker build -f $DOCKERFILE $BUILD_OPTIONS $BUILD_ARGS -t $TAG $SOURCE_DIR $NO_CACHE 

{ set +x; } 2>/dev/null
