# oc-h265-ssd-mobilenet-v1-coco-efficientnet-b1

Object detection pipeline taking encoded video frames in h265 format and using [ssd-mobilenet-v1-coco](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/ssd_mobilenet_v1_coco) for detection and [efficientnet-b1](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/efficientnet-b1) for classification.

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
objects

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
    ssd_mobilenet_v1_coco
    }

    state tensors_to_objects {
	direction LR
    labels_coco
    }

		scale --> csc
		csc --> inference
		inference --> tensors_to_objects
    }

state classify {
direction LR
    
    state scale_2 {
	direction LR
      w224xh224
    }
    state csc_2 {
	direction LR
    RGB
    }

    state inference_2 {
	direction LR
    efficientnet-b1
    }

    state tensors_to_attributes {
	direction LR
    labels_imagenet
    }
	    frames_1 --> crop
		objects_1 --> crop
	    crop --> scale_2
		scale_2 --> csc_2
		csc_2 --> inference_2
		inference_2 --> tensors_to_attributes
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
