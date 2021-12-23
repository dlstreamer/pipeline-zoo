# Use Case: Pick N Go

## Description of workload
Pick N Go is used to emulate and benchmark a retail shopping expereince.   
Consumers would pick an item for sale, from a self service kiosk, scan the product and checkout the item.   
    
This workload will be benchmarked on a TGL-i5 which would be explicitly   
set to a TDP of  
a) 15W    
b) 28W     

It would be rendering and playing 1 stream at a 4k resolution on the display screen.  
With the rendering stream running simultaneously we would start multiple streams to run inference until   
the system has saturated and the inference FPS per stream falls below the target FPS.   
   
## Steps to set-up the system
We benchmarked on 11th Gen Intel(R) Core(TM) i5-1145G7 @ 2.60GHz  TGL NUC

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

## Steps to run the workload

1. Build the docker image 
``` 
cd pipeline-zoo/tools/docker 
./build.sh
docker images 
``` 
This will list `media-analytics-pipeline-zoo 6.95GB` image
 
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
./run.sh
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
change the media file using --override media command line option.
 
This will launch DLStreamer/gvadetect for object detection task using FP16 quantized `od-h264-mbnetssd-v1-coco` model.
```
gst-launch-1.0 filesrc location=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/Pexels-Videos-1388365/disk/input/stream.fps.mp4 ! \
  qtdemux ! h264parse ! video/x-h264 ! vaapih264dec name=decode0 ! \ 
  gvadetect device=GPU ie-config=CLDNN_PLUGIN_THROTTLE=1 name=detect0 \ 
  model-proc=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco_INT8/FP16-INT8/ssd_mobilenet_v1_coco_INT8.json \
  model=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco/FP16/ssd_mobilenet_v1_coco.xml ! \
  gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines \
  file-path=<named_pipe>/output ! gvafpscounter ! fakesink sync=True async=false name=sink0

```
 

### Observe the GPU/CPU usage to confirm the setup is correct

#### Setup verification

 on terminal 1  
>sudo intel_gpu_top
 
 on terminal 2  
>sudo htop

on terminal 3    
>Observe the FPS reported by pipeline-zoo pipebench

