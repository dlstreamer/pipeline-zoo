# oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf

Object detection pipeline taking encoded video frames in h264 format and using [ssd-mobilenet-v1-coco]() for detection and [resnet-50-tf]() for classification.

# TODO: Diagram Update

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
      w300xh300
    }
    state csc {
    BGR
    }

    state inference {
    mbnetssd
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
