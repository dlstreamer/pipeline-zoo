#!/bin/bash

WORK_DIR=$(dirname $(readlink -f "$0"))
INTERACTIVE=--non-interactive
CI=
ENVIRONMENT=
ENTRYPOINT_ARGS='--entrypoint-args -i --entrypoint-args -c --entrypoint-args /home/pipeline-zoo/tools/tests/pytest.sh'
ENTRYPOINT="--entrypoint /bin/bash"

#Get options passed into script
function get_options {
  while :; do
    case $1 in
      -h | -\? | --help)
        show_help
        exit
        ;;
      --image)
        if [ "$2" ]; then
          IMAGE=$2
          shift
        else
          error "Image expects a value"
        fi
        ;;
      --pytest-args|--pytest-arg|--pylint-arg)
        if [ "$2" ]; then
          ENTRYPOINT_ARGS+="--entrypoint-args $2 "
          shift
        else
          error "Pytest-args expects a value"
        fi
        ;;
      --pylint)
        ENTRYPOINT="--entrypoint ./tests/pylint.sh"
        ;;
      --interactive)
        unset INTERACTIVE
        ;;
      --ci)
        CI="-e TEAMCITY_VERSION=2019.1.3"
        ;;
      -e)
        if [ "$2" ]; then
          ENVIRONMENT+="-e $2 "
          shift
        else
          error "Environment expects a value"
        fi
        ;;
      *)
        break
        ;;
    esac

    shift
  done
}

function show_help {
  echo "usage: run.sh"
  echo "  [ --image : Specify the image to run the tests on ]"
  echo "  [ --pylint : Run the pylint test ] "
  echo "  [ --interactive : Run interactively ] "
  echo "  [ --ci : Output results for Team City integration ] "
  echo "  [ -e : Add environment variable to container ] "
}

function error {
    printf '%s\n' "$1" >&2
    exit
}

get_options "$@"

#If tag is not used, set VA_SERVING_TAG to default
if [ -z "$IMAGE" ]; then
  IMAGE=media-analytics-pipeline-zoo:latest
fi

$WORK_DIR/../docker/run.sh --image $IMAGE  \
  $DEV $CI $ENVIRONMENT $INTERACTIVE $ENTRYPOINT $ENTRYPOINT_ARGS
