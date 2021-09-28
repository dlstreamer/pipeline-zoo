# decode-h264-300x300

Decode VPP  pipeline taking encoded video frames in h264 format and resizing

```mermaid
stateDiagram
    state Decode-VPP {
	
	state media {
		h264
	}
	
    state video_source {
		demux --> parse 
    }
	
	state vpp {
	      scale
	}
	
	state scale {
	   w300xh300
	}
		
	media --> video_source
    video_source --> decode
	decode --> vpp
    vpp --> frames
} 
```


