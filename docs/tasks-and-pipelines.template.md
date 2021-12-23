# Tasks and Pipelines

Pipelines are organized according to the task they perform. Tasks are
defined based on the types of input they accept and the types of
output they generate. They specify the overall general topology of a
pipeline. Pipelines within a task further specficy the model,
algorithms and media formats used to perform a task. Each pipeline has
well defined semantics that can be used to compare the performance and
accuracy of different implementations and platforms. 

## Pipeline Taxonomy

```mermaid
graph TB
  Base[Pipeline Zoo] --> Video
  subgraph "Input Type"
  Video
  end
  Video --> Object_Detection
  Video --> Object_Classification
  Video --> Decode_VPP
  Object_Detection --> od-h264-ssd-mobilenet-v1-coco
  Object_Classification --> oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf
  Object_Classification --> oc-h264-full-frame-resnet-50-tf
  Decode_VPP --> decode-h264-bgra
  subgraph "Task"
  Object_Detection("Object Detection")
  Object_Classification("Object Classification")
  Decode_VPP("Decode VPP")
  end
  subgraph "Task"
  end
  subgraph "Pipeline"
  od-h264-ssd-mobilenet-v1-coco
  oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf
  oc-h264-full-frame-resnet-50-tf
  decode-h264-bgra
  end
```

## [Object Detection](../pipelines/video/object-detection)

Object detection pipelines take encoded video frames and produce bounding boxes of regions of interest and corresponding labels.

![diagram](../pipelines/video/object-detection/README-1.svg)

## [Object Classification](../pipelines/video/object-classification)
Object classification pipelines take encoded video frames and produce bounding boxes of regions of interest with labels and attributes.
Object classification pipelines include a detection model and one or multiple classification models.

![diagram](../pipelines/video/object-classification/README-1.svg)


## [Decode VPP](../pipelines/video/decode-vpp)

Decode VPP pipelines take encoded video frames and produce raw frames
after performing crop, scale and color space conversion.

![diagram](../pipelines/video/decode-vpp/README-1.svg)
