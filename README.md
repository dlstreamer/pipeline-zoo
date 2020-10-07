# Getting Started
## Installation 
1. Clone Repo
   ```
   git clone https://gitlab.devtools.intel.com/media-analytics-pipeline-zoo/pipeline-zoo.git
   ```
2. Build Pipeline Zoo Environment
   ```
   ./pipeline-zoo/tools/docker/build.sh 
   ```
   Output:
   ```
   Successfully built 113352079483
   Successfully tagged media-analytics-pipeline-zoo-bench:latest
   ```
3. Launch Pipeline Zoo
   ```
   ./pipeline-zoo/tools/docker/run.sh 
   ```
## Pipline Zoo Commands
### List Pipelines
   Command:
   ```
   pipebench list
   ```
   Output:
   ```
   pipebench list
   =======================
   Arguments for pipebench
   =======================
	workspace_root == .
	command == <function list_pipelines at 0x7fdbe4d65a60>

	+------------------+------------------+---------------+
	| pipeline         | task             | model         |
	+==================+==================+===============+
	| od-h264-yolov3   | object-detection | yolo-v3-tf    |
	+------------------+------------------+---------------+
	| od-h264-mbnetssd | object-detection | mobilenet-ssd |
	+------------------+------------------+---------------+
   ```
   
### Download Pipeline

   Command:
   ```
   pipebench download od-h264-mbnetssd
   ```
   Expected Output Tree:
   ```
    - pipeline-zoo/
      + pipelines/
      + runners/
      + tools/
      - workspace/
        - od-h264-mbnetssd/
          - media/
            - video/
              + 20200711_cat/
              + bottle_detection/
              + person-bicycle-car-detection/
         - models/
           - mobilenet-ssd/
             + FP16/
             + FP32/
             mobilenet-ssd.caffemodel
             mobilenet-ssd.json
             mobilenet-ssd.prototxt
         - runners/
           + dlstreamer/
           + mockrun/
         README.md
         dlstreamer.config.yml
         media.list.yml
         mockrun.config.yml
         models.list.yml
         od-h264-mbnetssd.pipeline.yml
   ```
   
### Measure Pipeline Throughput
     
Command:
     
 ```
       pipebench measure od-h264-mbnetssd
 ```
   
Expected Output:
     
```
          =================
	  Frames Per Second
	  	  Stream: 0000 FPS:100.5469 Min: 88.5230 Max: 118.4075 Avg: 98.9552
	  =================

	  ==============================
	  Ended: pipebench memory source
	  	  Ended: 1602075186.5367947
		  Frames Written: 5960
	  ==============================

	  ============================
	  Ended: pipebench memory sink
	  	  Ended: 1602075186.64656
		  Frames Read: 5960
	  ============================

	  pipeline          runner      media                                 avg FPS (selected)
	  ----------------  ----------  ----------------------------------  --------------------
	  od-h264-mbnetssd  dlstreamer  video/person-bicycle-car-detection               98.9552
```
     
### Measure Pipeline Density

Command:
```
 pipebench measure od-h264-mbnetssd --density
```
      
Expected Output:
      
```
	     ==============
	     Density Result
		     Stream: 0000 avg:(27.131767701626966, False)
		     Stream: 0001 avg:(26.64521668312581, False)
		     Stream: 0002 avg:(25.848245068960324, False)
		     Stream: 0003 avg:(25.947736259217095, False)
		     Stream: 0004 avg:(25.7801414724865, False)
		     Stream: 0005 avg:(25.808106633418532, False)
		     Stream: 0006 avg:(26.325975123855283, False)
	     ==============

	     ==============
	     Stream Density
		     Iteration: 3
		     Number of Streams: 7
		     Passed: False
	     ==============

	    pipeline          runner      media                                 density
	    ----------------  ----------  ----------------------------------  ---------
	    od-h264-mbnetssd  dlstreamer  video/person-bicycle-car-detection          6
```

### Configure DL Streamer Runner
Command:
```
 pipebench measure od-h264-mbnetssd --runner-override detect.nireq 1 --runner-override detect.cpu-throughput-streams 5
```
   
Expected Change in gst-launch
   
Location:
```
 pipeline-zoo/workspace/od-h264-mbnetssd/runners/dlstreamer/results/default/throughput/default.gst-launch.sh
```

gst-launch command:

```
 gst-launch-1.0 filesrc location=/tmp/1510b74e-08ad-11eb-968e-1c697a06fd65/input ! video/x-h264 ! h264parse ! video/x-h264, stream-format=(string)byte-stream, alignment=(string)au, level=(string)4, profile=(string)high, width=(int)1920, height=(int)1080, framerate=(fraction)24/1, pixel-aspect-ratio=(fraction)1/1, interlace-mode=(string)progressive, chroma-format=(string)4:2:0, bit-depth-luma=(uint)8, bit-depth-chroma=(uint)8, parsed=(boolean)true ! avdec_h264 name=decode max-threads=1 ! gvadetect inference-interval=1 nireq=1 cpu-throughput-streams=5 name=detect model-proc=/home/pipeline-zoo/workspace/od-h264-mbnetssd/models/mobilenet-ssd/mobilenet-ssd.json model=/home/pipeline-zoo/workspace/od-h264-mbnetssd/models/mobilenet-ssd/FP32/mobilenet-ssd.xml ! gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/1510b74e-08ad-11eb-968e-1c697a06fd65/output ! gvafpscounter ! fakesink
```

### Download second pipeline
Command:
```
 pipebench download od-h264-yolov3
```
 
Expected Output Tree:
    
```
       - pipeline-zoo/
         + pipelines/
         + runners/
         + tools/
         - workspace/
           + od-h264-mbnetssd/
           - od-h264-yolov3/
             - media/
               - video/
                 + 20200711_dog_bark/
                 + classroom/
                 + person-bicycle-car-detection/
            - models/
               + yolo-v3-tf/
             - runners/
               + dlstreamer/
               + mockrun/
             README.md
             dlstreamer.config.yml
             media.list.yml
             mockrun.config.yml
             models.list.yml
             od-h264-yolov3.pipeline.yml
```
### Measure throughput for second pipeline

Command:
```
 pipebench measure od-h264-yolov3
```

Expected Output:
```
    pipeline        runner      media                                 avg FPS (selected)
    --------------  ----------  ----------------------------------  --------------------
    od-h264-yolov3  dlstreamer  video/person-bicycle-car-detection               44.8486
```

# Generated Files

| path | description|
|---------------| ---| 
|`workspace/<pipeline_name>` | downloaded pipeline |
|`workspace/<pipeline_name>/workloads` | generated reference data for workload | 
|`workspace/<pipeline_name>/runners/<runner_name>`| runner applicaiton and configuration files |
|`workspace/<pipeline_name>/runners/<runner_name>/results/<workload_name>/throughput` | throughput results |
|`workspace/<pipeline_name>/runners/<runner_name>/results/<workload_name>/density` | density results |
|`workspace/<pipeline_name>/runners/<runner_name>/results/<workload_name>/throughput/<workload_name>.gst-launch.sh` | runner command line |




