# Object Detection

Object detection pipelines take encoded video frames and produce bounding boxes of regions of interest and corresponding labels.


```mermaid
stateDiagram
    direction LR 
    state Object-Detection {
    direction LR
    state video_source {
	direction LR
		demux --> parse 
    }
   
    state detect {
	direction LR
		scale --> csc
		csc --> inference
		inference --> tensors_to_objects
    }
    
    media --> video_source
    video_source --> decode
    decode --> detect
    detect --> objects
} 
```
