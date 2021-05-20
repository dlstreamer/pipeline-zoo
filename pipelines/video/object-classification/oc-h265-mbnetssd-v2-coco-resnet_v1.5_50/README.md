# oc-h265-mbnetssd-v2-coco-resnet_v1.5_50

Object detection pipeline taking encoded video frames in h265 format and using [mobilenet ssd]() for detection and resnet for classification.

# TODO: Update Diagram

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
