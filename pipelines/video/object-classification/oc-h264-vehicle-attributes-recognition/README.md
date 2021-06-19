# oc-h264-vehicle-attributes-recognition

Object classification pipeline taking encoded video frames in h264 format and using [od-h264-person-vehicle-bike-detection-crossroad-0078]() for detection.

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
      w1024xh1024
    }
    state csc {
    BGR
    }

    state inference {
    person_vehicle_bike_detection_crossroad_0078
    }

    state tensors_to_objects {
    labels_person_vehicle_bike
    }

		scale --> csc
		csc --> inference
		inference --> tensors_to_objects
    }
	
	state classify {
	    state crop {
		}
	    state scale {
		 w72x72
		}
		state csc {
		BGR
		}
		state inference {
		vehicle_attributes_recognition_barrier_0039
		}
		state tensors_to_attributes {
		labels_vehicle_type_color
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
