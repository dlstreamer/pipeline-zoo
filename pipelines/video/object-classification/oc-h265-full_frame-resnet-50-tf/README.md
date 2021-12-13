# oc-h265-full_frame-resnet-50-tf

Object classification pipeline taking encoded video frames in h265 format and using [resnet-50-tf]() for full frame classification.

```mermaid
stateDiagram
 
    state Object-Classification {
  
    state media {
		h265
    }

    state video_source {
		demux --> parse 
    }
frames
objects
state detect {
  full_frame
}
state classify {
    state scale {
      w224xh224
    }
    state csc {
    RGB
    }

    state inference {
    resnet-50-tf
    }

    state tensors_to_attributes {
    labels_imagenet
    }
        frames --> scale 
		scale --> csc
		csc --> inference
		inference --> tensors_to_attributes
    }
    
    media --> video_source
    video_source --> decode
    decode --> detect
	detect --> objects
	detect --> frames
	frames --> classify
	objects --> classify
    classify --> objects_attributes
} 
```
