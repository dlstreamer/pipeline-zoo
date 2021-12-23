#!/bin/bash -e
#
# Copyright (C) 2019-2021 Intel Corporation.
#
# SPDX-License-Identifier: MIT
#
DOCS_DIR=$(dirname "$(readlink -f "$0")")
SOURCE_DIR=$(dirname $DOCS_DIR)


docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/docs/tasks-and-pipelines.template.md -o /data/docs/tasks-and-pipelines.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/decode-vpp/README.template.md -o /data/pipelines/video/decode-vpp/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/decode-vpp/decode-h265/README.template.md -o /data/pipelines/video/decode-vpp/decode-h265/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/decode-vpp/decode-h264-bgra/README.template.md -o /data/pipelines/video/decode-vpp/decode-h264-bgra/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-classification/README.template.md -o /data/pipelines/video/object-classification/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-classification/oc-h264-full_frame-resnet-50-tf/README.template.md -o /data/pipelines/video/object-classification/oc-h264-full_frame-resnet-50-tf/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-classification/oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf/README.template.md -o /data/pipelines/video/object-classification/oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-classification/oc-h265-full_frame-resnet-50-tf/README.template.md -o /data/pipelines/video/object-classification/oc-h265-full_frame-resnet-50-tf/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-classification/oc-h265-ssd-mobilenet-v1-coco-resnet-50-tf/README.template.md -o /data/pipelines/video/object-classification/oc-h265-ssd-mobilenet-v1-coco-resnet-50-tf/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-detection/README.template.md -o /data/pipelines/video/object-detection/README.md


docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-detection/od-h264-ssd-mobilenet-v1-coco/README.template.md -o /data/pipelines/video/object-detection/od-h264-ssd-mobilenet-v1-coco/README.md

docker run -it --user 1000 -v $SOURCE_DIR:/data minlag/mermaid-cli -i /data/pipelines/video/object-detection/od-h265-ssd-mobilenet-v1-coco/README.template.md -o /data/pipelines/video/object-detection/od-h265-ssd-mobilenet-v1-coco/README.md

