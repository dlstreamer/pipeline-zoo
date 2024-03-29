# od-h265-yolo-v4-tf-416

Object detection pipeline taking encoded video frames in h265 format and using [yolo-v4-tf]() for detection.

```mermaid
stateDiagram

    state Object-Detection {

    state media {
    h265
    }

    state video_source {
		demux --> parse
    }

    state detect {
    state scale {
      w416xh416
    }
    state csc {
    RGB
    }

    state inference {
    yolo_v4_tf
    }

    state tensors_to_objects {
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
