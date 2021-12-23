# Object Classification

Object classification pipelines take encoded video frames and produce bounding boxes of regions of interest with labels and attributes.
Object classification pipelines include a detection model and one or multiple classification models.


```mermaid
stateDiagram
    direction LR
    state Object-Classification {
	direction LR
    state video_source {
	direction LR
		demux --> parse 
    }
	frames
	state classify {
	direction LR
		frames_1 --> crop_1
		objects_1 --> crop_1
		crop_1 --> scale_2
		scale_2 --> csc_2
		csc_2 --> inference_2
		inference_2 --> tensors_to_attributes_1
	}
    
    state detect {
	direction LR
		scale --> csc
		csc --> inference
		inference --> tensors_to_objects
    }
	
	state classify_N {
	direction LR
		frames_N --> crop_N
		objects_N --> crop_N
		crop_N --> scale_N
		scale_N --> csc_N
		csc_N --> inference_N
		inference_N --> tensors_to_attributes_N
	}
    state fork <<fork>>
	state join <<join>>
	objects-->fork
	frames-->fork
    media --> video_source
    video_source --> decode
    decode --> detect
    detect --> objects
	detect --> frames
	fork --> classify
	fork --> classify_N
	classify --> join 
	classify_N --> join 
	join --> objects_attributes
} 
```



