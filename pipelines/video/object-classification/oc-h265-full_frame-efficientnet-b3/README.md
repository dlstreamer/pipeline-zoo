# oc-h265-full_frame-efficientnet-b0

Object classification pipeline taking encoded video frames in h265 format and using [efficientnet-b0](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/efficientnet-b0) for full frame classification.

```mermaid
stateDiagram
    direction LR  
    state Object-Classification {
    direction LR
    state media {
	direction LR
		h265
    }

    state video_source {
	direction LR
		demux --> parse 
    }
frames
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
    decode --> frames
	frames --> classify
    classify --> full_frame_attributes
} 
```
