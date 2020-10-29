# Object Classification

Object classification pipelines take encoded video frames and produce bounding boxes of regions of interest with labels and attributes.
Object classification pipelines include a detection model and one or multiple classification models that classify attributes of detected regions.


```mermaid
stateDiagram
    state Object-Classification {
    state video_source {
		demux --> parse 
    }
	frames
	state classify {
		frames --> crop
		regions --> crop
		crop --> scale
		scale --> csc
		csc --> inference
		inference --> tensors_to_attributes
	}
    
    state detect {
		scale --> csc
		csc --> inference
		inference --> tensors_to_objects
    }
	
	state classify_N {
		frames --> crop
		regions --> crop
		crop --> scale
		scale --> csc
		csc --> inference
		inference --> tensors_to_attributes
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



