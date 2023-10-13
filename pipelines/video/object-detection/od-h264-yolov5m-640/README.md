# od-h264-yolov5m-640

Object detection pipeline taking encoded video frames in h264 format and using [yolov5m-640_INT8](https://github.com/dlstreamer/pipeline-zoo-models/tree/main/storage/yolov5m-640_INT8) or [yolov5m-640](https://github.com/dlstreamer/pipeline-zoo-models/tree/main/storage/yolov5m-640) for detection.

```mermaid
stateDiagram
    direction LR
    state Object-Detection {
    direction LR
    state media {
	direction LR
    h264
    }

    state video_source {
	direction LR
		demux --> parse
    }

    state detect {
	direction LR
    state scale {
	direction LR
      w640xh640
    }
    state csc {
	direction LR
    BGR
    }

    state inference {
	direction LR
	yolov5m-640
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
