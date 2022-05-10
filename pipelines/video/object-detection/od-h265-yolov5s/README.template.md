# od-h265-yolov5s

Object detection pipeline taking encoded video frames in h265 format and using [yolov5s]() for detection.

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
      w640xh640
    }
    state csc {
	direction LR
    BGR
    }

    state inference {
	direction LR
    yolov5n
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
