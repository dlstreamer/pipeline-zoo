#!/bin/bash -e
#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#
BASE_IMAGE=openvino/ubuntu18_data_dev:2021.1
#BASE_IMAGE=openvisualcloud/xeone3-ubuntu1804-analytics-dev:20.4
BASE_BUILD_CONTEXT=
BASE_BUILD_DOCKERFILE=
BASE_BUILD_TAG=
USER_BASE_BUILD_ARGS=
TAG=
RUN_PREFIX=
TARGET=
ENVIRONMENT_FILES=()

DOCKERFILE_DIR=$(dirname "$(readlink -f "$0")")
SOURCE_DIR=$(dirname $DOCKERFILE_DIR)
BUILD_ARGS=$(env | cut -f1 -d= | grep -E '_(proxy|REPO|VER)$' | sed 's/^/--build-arg / ' | tr '\n' ' ')
BASE_BUILD_ARGS=$(env | cut -f1 -d= | grep -E '_(proxy|REPO|VER)$' | sed 's/^/--build-arg / ' | tr '\n' ' ')
BUILD_OPTIONS="--network=host"

DEFAULT_BASE_BUILD_CONTEXT="https://github.com/OpenVisualCloud/Dockerfiles.git#v20.4:XeonE3/ubuntu-18.04/analytics/dev"
DEFAULT_BASE_BUILD_DOCKERFILE="Dockerfile"
DEFAULT_BASE_BUILD_TAG="media-analytics-pipeline-zoo-base"
DEFAULT_BASE_BUILD_ARGS=""

get_options() {
    while :; do
        case $1 in
        -h | -\? | --help)
            show_help
            exit
            ;;
        --base)
            if [ "$2" ]; then
                BASE_IMAGE=$2
                shift
            else
                error 'ERROR: "--base" requires an argument.'
            fi
            ;;
        --target)
            if [ "$2" ]; then
                TARGET="--target $2"
                shift
            else
                error 'ERROR: "--target" requires an argument.'
            fi
            ;;
        --base-build-context)
            if [ "$2" ]; then
                BASE_BUILD_CONTEXT=$2
                shift
            else
                error 'ERROR: "--base-build-context" requires an argument.'
            fi
            ;;
        --base-build-dockerfile)
            if [ "$2" ]; then
                BASE_BUILD_DOCKERFILE=$2
                shift
            else
                error 'ERROR: "--base-build-dockerfile" requires an argument.'
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
        --base-build-arg)
            if [ "$2" ]; then
                USER_BASE_BUILD_ARGS+="--build-arg $2 "
                shift
            else
                error 'ERROR: "--base-build-arg" requires an argument.'
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
        --dockerfile-dir)
            if [ "$2" ]; then
                DOCKERFILE_DIR=$2
                shift
            else
                error 'ERROR: "--dockerfile-dir" requires an argument.'
            fi
            ;;
	--environment-file)
            if [ "$2" ]; then
                ENVIRONMENT_FILES+=($2)
                shift
            else
                error 'ERROR: "--environment-file" requires an argument.'
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

    if [[ -n "$BASE_BUILD_CONTEXT" && -z "$BASE_BUILD_DOCKERFILE" ]]; then
        error 'ERROR: setting "--base-build-context" requires setting "--base-build-dockerfile"'
    elif [[ -z "$BASE_BUILD_CONTEXT" && -n "$BASE_BUILD_DOCKERFILE" ]]; then
        error 'ERROR: setting "--base-build-dockerfile" requires setting "--base-build-context"'
    fi

    if [ -z "$BASE_IMAGE" ]; then
        BASE="BUILD"
        if [ -z "$BASE_BUILD_CONTEXT" ]; then
            BASE_BUILD_CONTEXT=$DEFAULT_BASE_BUILD_CONTEXT
        fi
        if [ -z "$BASE_BUILD_DOCKERFILE" ]; then
            BASE_BUILD_DOCKERFILE=$DEFAULT_BASE_BUILD_DOCKERFILE
        fi
        if [ -z "$BASE_BUILD_TAG" ]; then
            BASE_BUILD_TAG=$DEFAULT_BASE_BUILD_TAG
        fi
        if [ -z "$USER_BASE_BUILD_ARGS" ]; then
            USER_BASE_BUILD_ARGS=$DEFAULT_BASE_BUILD_ARGS
        fi
        BASE_BUILD_ARGS+=$USER_BASE_BUILD_ARGS
    else
        BASE="IMAGE"
    fi

    if [ -z "$TAG" ]; then
        TAG="media-analytics-pipeline-zoo-bench"
    fi
}

show_base_options() {
    echo ""
    echo "Building Base Image: '${BASE_BUILD_TAG}'"
    echo ""
    echo "   Build Context: '${BASE_BUILD_CONTEXT}'"
    echo "   Dockerfile: '${BASE_BUILD_DOCKERFILE}'"
    echo "   Build Options: '${BUILD_OPTIONS}'"
    echo "   Build Arguments: '${BASE_BUILD_ARGS}'"
    echo ""
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
    echo "   Target: '${TARGET}'"
    echo "   Environment Files: '${ENVIRONMENT_FILE_LIST}'"
    echo ""
}

show_help() {
    echo "usage: build.sh"
    echo "  [--base base image]"
    echo "  [--build-arg additional build args to pass to docker build]"
    echo "  [--base-build-arg additional build args to pass to docker build for base image]"
    echo "  [--base-build-context context of docker build for base image]"
    echo "  [--base-build-dockerfile dockerfile used to build base image]"
    echo "  [--tag tag for image]"
    echo "  [--target build a specific target]"
    echo "  [--dockerfile-dir specify a different dockerfile directory]"
    echo "  [--environment-file read and set environment variables from a file. Can be supplied multiple times.]"
    echo "  [--dry-run print docker commands without running]"
    exit 0
}

error() {
    printf '%s %s\n' "$1" "$2" >&2
    exit 1
}

get_options "$@"

# BUILD BASE IF BASE IS NOT SUPPLIED

if [ "$BASE" == "BUILD" ]; then
    show_base_options

    if [ -z "$RUN_PREFIX" ]; then
        set -x
    fi

    $RUN_PREFIX docker build "$BASE_BUILD_CONTEXT" -f "$BASE_BUILD_DOCKERFILE" $BUILD_OPTIONS $BASE_BUILD_ARGS -t $BASE_BUILD_TAG

    { set +x; } 2>/dev/null
    BASE_IMAGE=$BASE_BUILD_TAG
fi

# BUILD IMAGE

BUILD_ARGS+=" --build-arg BASE=$BASE_IMAGE "

#cp -f $DOCKERFILE_DIR/Dockerfile $DOCKERFILE_DIR/Dockerfile.env
#ENVIRONMENT_FILE_LIST=

#if [[ "$BASE_IMAGE" == "openvino/"* ]]; then
#    $RUN_PREFIX docker run -t --rm --entrypoint /bin/bash -e HOME=/root -e HOSTNAME=BASE $BASE_IMAGE "-i" "-c" "env" > $DOCKERFILE_DIR/openvino_base_environment.txt
#    ENVIRONMENT_FILE_LIST+="$DOCKERFILE_DIR/openvino_base_environment.txt "
#fi

#for ENVIRONMENT_FILE in ${ENVIRONMENT_FILES[@]}; do
 #   if [ ! -z "$ENVIRONMENT_FILE" ]; then
#	ENVIRONMENT_FILE_LIST+="$ENVIRONMENT_FILE "
 #   fi
#done

#if [ ! -z "$ENVIRONMENT_FILE_LIST" ]; then
#    cat $ENVIRONMENT_FILE_LIST | grep -E '=' | tr '\n' ' ' | tr '\r' ' ' > $DOCKERFILE_DIR/final.env
#    echo "ENV " | cat - $DOCKERFILE_DIR/final.env | tr -d '\n' >> $DOCKERFILE_DIR/Dockerfile.env
#fi


show_image_options

if [ -z "$RUN_PREFIX" ]; then
    set -x
fi

$RUN_PREFIX docker build -f "$DOCKERFILE_DIR/Dockerfile" $BUILD_OPTIONS $BUILD_ARGS -t $TAG $TARGET $SOURCE_DIR

{ set +x; } 2>/dev/null
