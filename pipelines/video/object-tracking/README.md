# Object Track

Object tracking pipeline processes decoded video frames scaled to HD resolution, produces detected objects as regions of interest with detection model, generates unique embedding with reidentification model and assign tracking id for each ROI and encodes video stream with HEVC.

```mermaid
stateDiagram
    direction LR 
    state Object-Tracking {
    direction LR
    state video_source {
	direction LR
		demux --> parse 
    }

    
    media --> video_source
    video_source --> decode
    decode --> detect
    detect --> inference
    inference --> track
    track --> objects
} 
```