# od-h264-yolo-v2-ava-0001

Object detection pipeline taking encoded video frames in h264 format and using [yolo-v3-tf]() for detection.

```mermaid
stateDiagram
 
    state Object-Detection {
  
    state media {
    h264
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
    yolo-v2-ava-0001
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
