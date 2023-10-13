# od-h265-yolov5m-416

Object detection pipeline taking encoded video frames in h265 format and using [yolov5m-416](https://github.com/dlstreamer/pipeline-zoo-models/tree/main/storage/yolov5m-416) or [yolov5m-41_INT8_](https://github.com/dlstreamer/pipeline-zoo-models/tree/main/storage/yolov5m-416_INT8) for detection.

```mermaid
stateDiagram
    direction LR
    state Object-Detection {
    direction LR
    state media {
	direction LR
    h265
    }

    state video_source {
	direction LR
		demux --> parse
    }

    state detect {
	direction LR
    state scale {
	direction LR
      w416xh416
    }
    state csc {
	direction LR
    BGR
    }

    state inference {
	direction LR
	yolov5m-416
    }

    state tensors_to_objects {
	direction LR
    labels_coco
    }

		scale --> csc
		csc --> inference
		inference --> tensors_to_objects
    }

    media --> video_source
    video_source --> decode
    decode --> detect
    detect --> objects
}
```
