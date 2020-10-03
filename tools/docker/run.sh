#!/bin/bash -e
#
# Copyright (C) 2019-2020 Intel Corporation.
#
# SPDX-License-Identifier: BSD-3-Clause
#

IMAGE=
VOLUME_MOUNT=
PORTS=
DEVICES=
DEFAULT_IMAGE="media-analytics-pipeline-zoo-bench"
ENTRYPOINT=
ENTRYPOINT_ARGS=
PRIVILEGED=
NETWORK=
USER=
ATTACH=

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
SOURCE_DIR=$(dirname "$SCRIPT_DIR")
SOURCE_DIR=$(dirname "$SOURCE_DIR")
ENVIRONMENT=$(env | cut -f1 -d= | grep -E '_(proxy)$' | sed 's/^/-e / ' | tr '\n' ' ')
ENVIRONMENT+="-e DISPLAY "

get_options() {
    while :; do
        case $1 in
        -h | -\? | --help)
            show_help # Display a usage synopsis.
            exit
            ;;
        --image) # Takes an option argument; ensure it has been specified.
            if [ "$2" ]; then
                IMAGE=$2
                shift
            else
                error 'ERROR: "--image" requires a non-empty option argument.'
            fi
            ;;
        --user)
            if [ "$2" ]; then
                USER="--user $2"
                shift
            else
                error 'ERROR: "--models" requires a non-empty option argument.'
            fi
            ;;
        -e)
            if [ "$2" ]; then
                ENVIRONMENT+="-e $2 "
                shift
            else
                error 'ERROR: "-e" requires a non-empty option argument.'
            fi
            ;;
        --entrypoint-args)
            if [ "$2" ]; then
                ENTRYPOINT_ARGS+="$2 "
                shift
            else
                error 'ERROR: "--entrypoint-args" requires a non-empty option argument.'
            fi
            ;;
        -p)
            if [ "$2" ]; then
                PORTS+="-p $2 "
                shift
            else
                error 'ERROR: "-p" requires a non-empty option argument.'
            fi
            ;;
        -v)
            if [ "$2" ]; then
                VOLUME_MOUNT+="-v $2 "
                shift
            else
                error 'ERROR: "-v" requires a non-empty option argument.'
            fi
            ;;
        --name)
            if [ "$2" ]; then
                NAME=$2
                shift
            else
                error 'ERROR: "--name" requires a non-empty option argument.'
            fi
            ;;
        --network)
            if [ "$2" ]; then
                NETWORK="--network $2"
                shift
            else
                error 'ERROR: "--network" requires a non-empty option argument.'
            fi
            ;;
        --entrypoint)
            if [ "$2" ]; then
                ENTRYPOINT="--entrypoint $2"
                shift
            else
                error 'ERROR: "--entrypoint" requires a non-empty option argument.'
            fi
            ;;
	--attach)
	    ATTACH=TRUE
            ;;
        --) # End of all options.
            shift
            break
            ;;
        -?*)
            printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
            ;;
        *) # Default case: No more options, so break out of the loop.
            break ;;
        esac

        shift
    done

    if [ -z "$IMAGE" ]; then
        IMAGE=$DEFAULT_IMAGE
    fi

    if [ -z "$NAME" ]; then
        # Convert tag separator if exists
        NAME=${IMAGE//[\:]/_}
    fi

}

show_options() {
    echo ""
    echo "Running Media Analytics Pipeline Zoo Image: '${IMAGE}'"
    echo "   Environment: '${ENVIRONMENT}'"
    echo "   Volume Mounts: '${VOLUME_MOUNT}'"
    echo "   Ports: '${PORTS}'"
    echo "   Name: '${NAME}'"
    echo "   Network: '${NETWORK}'"
    echo "   Entrypoint: '${ENTRYPOINT}'"
    echo "   EntrypointArgs: '${ENTRYPOINT_ARGS}"
    echo "   User: '${USER}'"
    echo "   Attach: '${ATTACH}'"
    echo ""
}

show_help() {
  echo "usage: run.sh" 
  echo "  [--image image]"
  echo "  [-v additional volume mount to pass to docker run]"
  echo "  [-e additional environment to pass to docker run]"
  echo "  [--entrypoint-args additional parameters to pass to entrypoint in docker run]"
  echo "  [-p additional ports to pass to docker run]"
  echo "  [--network name network to pass to docker run]"
  echo "  [--user name of user to pass to docker run]"
  echo "  [--name container name to pass to docker run]"
  echo "  [--attach attach to running container]"
  exit 0
}

error() {
    printf '%s\n' "$1" >&2
    exit
}

get_options "$@"

VOLUME_MOUNT+="-v $SOURCE_DIR:/home "
VOLUME_MOUNT+="-v /tmp:/tmp "
VOLUME_MOUNT+="-v /dev:/dev "
VOLUME_MOUNT+="-v /lib/modules:/lib/modules "
VOLUME_MOUNT+="-v $HOME/.Xauthority:/root/.Xauthority "

if [ -z "$NETWORK" ]; then
    NETWORK="--network=host"
fi

if [ -z "$ENTRYPOINT" ]; then
    ENTRYPOINT="--entrypoint /bin/bash"
fi

PRIVILEGED="--privileged "

show_options

if [ -z "$ATTACH" ]; then
    set -x
    docker run -it --rm $ENVIRONMENT $VOLUME_MOUNT $DEVICES $NETWORK $PORTS $ENTRYPOINT --name ${NAME} ${PRIVILEGED} ${USER} $IMAGE ${ENTRYPOINT_ARGS}
     { set +x; } 2>/dev/null
else
    RUNNING_INSTANCE=$(docker ps -q --filter "name=$IMAGE")
    if [ ! -z "$RUNNING_INSTANCE" ]; then
	set -x
	docker attach $RUNNING_INSTANCE
	{ set +x; } 2>/dev/null
    else
	error 'No Running Instance found'
    fi
fi
