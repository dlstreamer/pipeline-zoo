# oc-h265-full_frame-resnet-50-tf

Object classification pipeline taking encoded video frames in h265 format and using [resnet-50-tf](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/resnet-50-tf) for full frame classification.

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
    resnet_50_tf
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
    decode --> classify
    classify --> objects_attributes
} 
```
