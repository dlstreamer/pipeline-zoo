# oc-h265-full_frame-resnet-50-efficientnet-b3

Object full frame classification pipeline taking encoded video frames in h265 format and using [efficientnet-b3, resnet-50-pytorch] for full frame classification.

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
    state scale_csc {
	direction LR
      w224xh224_RGBP
    }

    state inference {
	direction LR
    resnet_50/efficientnet_b3
    }

    state tensors_to_attributes {
	direction LR
    labels_imagenet
    }
		scale_csc --> inference
		inference --> tensors_to_attributes
    }
    classify --> frames
    classify --> objects_attributes

    media --> video_source
    video_source --> decode
    decode --> classify0_resnet_50
    classify0_resnet_50 --> classify1_resnet_50
    classify1_resnet_50 --> classify2_efficientnet_b3
    classify2_efficientnet_b3 --> classify3_efficientnet_b3
    classify3_efficientnet_b3 --> classify4_efficientnet_b3
    classify4_efficientnet_b3 --> sink
} 

```
