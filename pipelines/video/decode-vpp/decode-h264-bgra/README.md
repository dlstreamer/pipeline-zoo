# decode-h264-i420

Decode VPP  pipeline taking encoded video frames in h264 format, decoding and converting to bgra frames.

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
	state csc {
		bgra
	}
	}
	
	media --> video_source
    video_source --> decode
    decode --> vpp
	vpp --> frames
} 
```


