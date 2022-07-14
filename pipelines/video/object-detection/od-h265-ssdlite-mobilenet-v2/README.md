# od-h265-ssdlite-mobilenet-v2

Object detection pipeline taking encoded video frames in h265 format and using [ssdlite_mobilenet_v2](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/ssdlite_mobilenet_v2) for detection.

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
    ssdlite_mobilenet_v2
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
