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
   =======================
   Arguments for pipebench
   =======================
	   workspace_root == .
	   command == <function list_pipelines at 0x7f7ca1ce8488>

   +--------------------------+-----------------------+------------------------------------+----------------+
   | Pipeline                 | Task                  | Models                             | Runners        |
   +==========================+=======================+====================================+================+
   | od-h264-yolov3           | object-detection      | yolo-v3-tf                         | dlstreamer     |
   |                          |                       |                                    | mockrun        |
   +--------------------------+-----------------------+------------------------------------+----------------+
   | od-h264-people           | object-detection      | person-detection-retail-0013       | opencv-gapi    |
   |                          |                       |                                    | dlstreamer     |
   |                          |                       |                                    | mockrun        |
   +--------------------------+-----------------------+------------------------------------+----------------+
   | od-h264-mbnetssd         | object-detection      | mobilenet-ssd                      | opencv-gapi    |
   |                          |                       |                                    | dlstreamer     |
   |                          |                       |                                    | mockrun        |
   +--------------------------+-----------------------+------------------------------------+----------------+
   | oc-h264-face-age-emotion | object-classification | face-detection-adas-0001           | opencv-gapi    |
   |                          |                       | age-gender-recognition-retail-0013 | dlstreamer     |
   |                          |                       | emotions-recognition-retail-0003   | mockrun        |
   +--------------------------+-----------------------+------------------------------------+----------------+
   
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
 pipeline-zoo/workspace/od-h264-mbnetssd/measurements/person-bicyle-car-detection/throughput/dlstreamer/person-bicycle-car-detection.gst-launch.sh
```

gst-launch command:

```
gst-launch-1.0 urisourcebin uri=file:///home/pipeline-zoo/workspace/od-h264-mbnetssd/media/video/person-bicycle-car-detection/person-bicycle-car-detection_1920_1080_2min.mp4 ! qtdemux ! parsebin ! avdec_h264 name=decode ! gvadetect name=detect model-proc=/home/pipeline-zoo/workspace/od-h264-mbnetssd/models/mobilenet-ssd/mobilenet-ssd.json model=/home/pipeline-zoo/workspace/od-h264-mbnetssd/models/mobilenet-ssd/FP32/mobilenet-ssd.xml ! gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/result.jsonl ! gvafpscounter ! fakesink
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
|`workspace/<pipeline_name>/runners/<runner_name>`| runner applications |
|`workspace/<pipeline_name>/measurements/<workload_name>/throughput/<runner_name>` | throughput results |
|`workspace/<pipeline_name>/measurements/<workload_name>/density.30fps/<runner-name>` | density results |
|`workspace/<pipeline_name>/measurements/<workload_name>/throughput/dlstreamer/<workload_name>.gst-launch.sh` | gstlaunch command line |

# [Additional Examples](./doc/examples.md)



