# od-h264-people

Object detection pipeline taking encoded video frames in h264 format and using [people-detection-retail-0013]() for detection.

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
      w320xh544
    }
    state csc {
    BGR
    }

    state inference {
    people_detection
    }

    state tensors_to_objects {
	person
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
