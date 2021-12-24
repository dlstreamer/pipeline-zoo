# Pick and Go Use Case

> **Note:**
> These instructions assume that you have
> followed the [getting started guide](../README.md#getting-started) for cloning
> and building the Pipeline Zoo Environement.
>These instructions have been tested on [11th Gen Intel(R) Core(TM) i5-1145G7 @ 2.60GHz TGL](https://ark.intel.com/content/www/us/en/ark/products/208660/intel-core-i51145g7-processor-8m-cache-up-to-4-40-ghz-with-ipu.html?wapkw=intel-core-i51145G7). 
>
> Actual results will vary based on configuation and the examples below are for illustration purposes only.


## Description

Pick and Go is used to simulate the media analytics pipelines used in a digital retail scenario.

Consumers would pick an item for sale from a self service kiosk, scan the product and checkout the item. 
    
## Media Analytics Pipelines

### Render x 1

To simulate the 4K rendering of a kiosk the Pick and Go use case uses
the [`decode-h265`](../pipelines/video/decode-vpp/decode-h265) pipeline. This pipeline is set to render a 4K
video to the screen.

![diagram](../pipelines/video/decode-vpp/decode-h265/README-1.svg)

### Object Detection x 8

To simulate detecting objects being scanned at the kiosk the Pick and
Go use case uses 8 streams of the
[`od-h264-ssd-mobilenet-v1-coco`](../pipelines/video/object-detection/od-h264-ssd-mobilenet-v1-coco)
pipeline. This pipeline detects objects in the streams using an `ssd-mobilenet-v1-coco` model.
	
![diagram](../pipelines/video/object-detection/od-h264-ssd-mobilenet-v1-coco/README-1.svg)
	
## System Configuration

The use case has been designed and tested to run on an 11th Gen Intel(R) Core(TM) i5-1145G7 @ 2.60GHz TGL
NUC with TDP settings as follows:

a) 15W    
b) 28W     

   
### Steps to set-up the system

1. Check the frequency of the system by running `lscpu` 

```
CPU MHz:                     2600.000  
CPU max MHz:                 4400.0000  
CPU min MHz:                 400.0000  
```

2. Set the TDP in the BIOS to 15W.
Enter the BIOS mode and select tab `Power` 
Package Power Limit 1 (Sustained) and Package Power Limit 2 (Burst Mode)
both must be set to 15 to enforce a 15W TDP.

3. Connect the system to a 4K resolution monitor screen

## Running the Use Case
 
2. Initialize the display port on the terminal environment  
>Set the display port as follows, for example if the display port is `:0`
```
tgli5@tgli5-Tiger-Lake-Client-Platform:~$ export DISPLAY=:0
tgli5@tgli5-Tiger-Lake-Client-Platform:~$ xhost +local:docker
```
If `:0` is not the display port then identify the correct 4k display port.

3. Play the 4k video on a X display window  
>Use pipebench to launch the rendering on the 4k display window  
```
./tools/docker/run.sh
pipebench run -vv --measure pick-and-go decode-h265
```
will launch the below command
```
gst-launch-1.0 -v \
 filesrc location=/home/pipeline-zoo/workspace/Marina-UHD-30FPS-HEVC-6Mbps-Landscape_9min.mp4 ! \
 qtdemux ! h265parse ! vaapih265dec ! queue ! fpsdisplaysink video-sink="vaapisink fullscreen=true" \
 sync=true text-overlay=false
```
This should launch the X window playing the 4K content.  
change the default media file using `--override media` command line option.
 
4. Play the inference pipeline in multiple streams  
>Open another terminal  
```
 docker exec -it media-analytics-pipeline-zoo bash
  
 pipebench run --measure pick-and-go od-h264-mbnetssd-v1-coco
```
 
This will launch the object detection task using FP16 quantized `ssd-mobilenet-v1-coco` model.
```
gst-launch-1.0 filesrc location=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/Pexels-Videos-1388365/disk/input/stream.fps.mp4 ! \
  qtdemux ! h264parse ! video/x-h264 ! vaapih264dec name=decode0 ! \ 
  gvadetect device=GPU ie-config=CLDNN_PLUGIN_THROTTLE=1 name=detect0 \ 
  model-proc=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco_INT8/FP16-INT8/ssd_mobilenet_v1_coco_INT8.json \
  model=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco/FP16/ssd_mobilenet_v1_coco.xml ! \
  gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines \
  file-path=<named_pipe>/output ! gvafpscounter ! fakesink sync=True async=false name=sink0

```
 
## Observe the GPU/CPU usage to confirm the setup is correct

### Setup verification

 on terminal 1  
>sudo intel_gpu_top
 
 on terminal 2  
>sudo htop

on terminal 3    
>Observe the FPS reported by pipeline-zoo pipebench

Example Output:
```
 Pipeline:
	od-h264-ssd-mobilenet-v1-coco

 Runner:
	dlstreamer
 	dlstreamer.pick-and-go.runner-settings.yml

 Media:
	video/Pexels-Videos-1388365

 Measurement:
	pick-and-go
 	pick-and-go.measurement-settings.yml

 Output Directory:
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/pick-and-go/dlstreamer/run-0002

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0008     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0008     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0008     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0008     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0008     0.0000    0.0000    0.0000     0.0000
======================================================================== 

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0008       0008    23.5491   23.8731   25.3064   190.9844
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0008       0008    23.5132   23.8281   25.2209   190.6250
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0008       0008    24.4750   24.7856   25.1385   192.2850
======================================================================== 

Pipeline                       Runner      Streams: 8
-----------------------------  ----------  ------------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 24.4750 Max: 25.1385 Avg: 24.7856 Total: 192.2850


```
