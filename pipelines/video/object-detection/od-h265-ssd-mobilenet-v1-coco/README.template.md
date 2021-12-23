# od-h265-ssd-mobilenet-v1-coco

Object detection pipeline taking encoded video frames in h265 format and using [ssd_mobilenet_v1_coco](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/ssd_mobilenet_v1_coco) for detection.

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
      w300xh300
    }
    state csc {
	direction LR
    BGR
    }

    state inference {
	direction LR
    ssd_mobilenet_v1_coco
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
