# Object Detection

Object detection pipelines take encoded video frames and produce bounding boxes of regions of interest and corresponding labels.

```mermaid
stateDiagram
    state Object_Detection {
        [*] --> encoded_frames
        encoded_frames --> decode
        decode --> scale
        scale --> CSC
        CSC --> detect
        detect --> objects
        objects --> [*]
    }
   
```
