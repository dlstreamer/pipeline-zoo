# decode-h265

Decode VPP  pipeline taking encoded video frames in h265 format and decode only

```mermaid
stateDiagram
    state Decode-VPP {
	
	state media {
	h265
	}
	
    state video_source {
		demux --> parse 
    }
		
	media --> video_source
    video_source --> decode
    decode --> frames
} 
```


