# oc-h264-full_frame-swin-tiny-patch4-window7-224

Object classification pipeline taking encoded video frames in h264 format and using [swin-tiny-patch4-window7-224](https://github.com/openvinotoolkit/open_model_zoo/tree/master/models/public/swin-tiny-patch4-window7-224) for full frame classification.

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
    swin_tiny_patch4_window7_224
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
