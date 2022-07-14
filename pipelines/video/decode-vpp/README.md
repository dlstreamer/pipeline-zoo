# Decode VPP

Decode VPP pipelines take encoded video frames and produce raw frames
after performing crop, scale and color space conversion.


```mermaid
stateDiagram
    direction LR
    state Decode-VPP {
	direction LR
    state video_source {
	direction LR
		demux --> parse 
    }
	
	state vpp {
	direction LR
		crop --> scale
		scale --> csc
	}
	
	media --> video_source
    video_source --> decode
    decode --> vpp
	vpp --> frames
} 
```



