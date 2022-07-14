# oc-h264-full_frame-efficientnet-b0

Object classification pipeline taking encoded video frames in h264 format and using [efficientnet-b0](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/efficientnet-b0) for full frame classification.

```mermaid
stateDiagram
    direction LR  
    state Object-Classification {
    direction LR
    state media {
	direction LR
		h264
    }

    state video_source {
	direction LR
		demux --> parse 
    }
frames
objects
state detect {
direction LR
  full_frame
}
state classify {
direction LR
    state scale {
	direction LR
      w224xh224
    }
    state csc {
	direction LR
    RGB
    }

    state inference {
	direction LR
    efficientnet_b0
    }

    state tensors_to_attributes {
	direction LR
    labels_imagenet
    }
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
