# oc-h264-yolov3-resnet_v1.5_50

Object classification pipeline taking encoded video frames in h264 format and using [yolov3]() for detection and resnet for classification.

```mermaid
stateDiagram
 
state Object-Classification {
  
  state media {
	h264
}

state video_source {
	demux --> parse 
}

frames
objects

state detect {
    state scale {
      w416xh416
    }
    state csc {
    BGR
    }

    state inference {
    yolo_v3
    }

    state tensors_to_objects {
    labels_coco
    }

		scale --> csc
		csc --> inference
		inference --> tensors_to_objects
    }
	
	state classify {
	    state crop {
		}
	    state scale {
		 w224xh224
		}
		state csc {
		RGB
		}
		state inference {
		resnet_v1_5_50
		}
		state tensors_to_attributes {
		labels_imagenet
		}
		frames --> crop
		regions --> crop
		crop --> scale
		scale --> csc
		csc --> inference
		inference --> tensors_to_attributes
	}
    frames --> classify
	objects --> classify
    media --> video_source
    video_source --> decode
    decode --> detect
    detect --> objects
	detect --> frames
	classify --> objects_attributes
} 
```
