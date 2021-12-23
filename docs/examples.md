# Examples

## View gst-launch command output corresponding to measurement

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --streams 1 -vv
```

Example Output:
```
 Pipeline:
	od-h264-ssd-mobilenet-v1-coco

 Runner:
	dlstreamer
 	dlstreamer.runner-settings.yml

 Media:
	video/person-bicycle-car-detection

 Measurement:
	throughput
 	throughput.measurement-settings.yml

 Output Directory:
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0000

=====================
Launching: dlstreamer
	Started: 1640291892.0147018
	Command: ['numactl', '--cpunodebind', '0', '--membind', '0', 'python3', 'dlstreamrun', '--systeminfo=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/systeminfo.json', '/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0000/iteration-0000/process-0000-stream-0000/throughput.piperun.yml']
=====================

=========================
Arguments for dlstreamrun
=========================
	systeminfo == /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/systeminfo.json
	piperun_config == /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0000/iteration-0000/process-0000-stream-0000/throughput.piperun.yml


No FP32-INT8 Model found, trying: FP32

gst-launch-1.0 filesrc location=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/input/stream.fps.mp4 ! qtdemux ! h264parse ! video/x-h264 ! avdec_h264 name=decode0 ! gvadetect device=CPU name=detect0 model-proc=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco_INT8/FP16-INT8/ssd_mobilenet_v1_coco_INT8.json model=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco/FP32/ssd_mobilenet_v1_coco.xml ! gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/3f04bbe2-6430-11ec-9045-1c697a06fd65/output ! gvafpscounter ! fakesink async=false name=sink0
```

## Fixed number of streams
```
pipebench run od-h264-ssd-mobilenet-v1-coco --streams 2
```
Output:
```
pipebench run od-h264-ssd-mobilenet-v1-coco --streams 2

 Pipeline:
	od-h264-ssd-mobilenet-v1-coco

 Runner:
	dlstreamer
 	dlstreamer.runner-settings.yml

 Media:
	video/person-bicycle-car-detection

 Measurement:
	throughput
 	throughput.measurement-settings.yml

 Output Directory:
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0001

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0002     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0002       0002    65.6073   67.4206   69.2338   134.8412
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0002       0002    64.2918   65.1374   65.9830   130.2748
======================================================================== 
```

## Running Standalone gst-launch

Generating a configuration file via the run command.

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco 
```

Run standalone `gst-launch.sh`, with throughput configuration

Command:

```
./od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0000/iteration-0000/process-0000-stream-0000/throughput.gst-launch.sh 
```

Example Output:

```
./od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0000/iteration-0000/process-0000-stream-0000/throughput.gst-launch.sh 
Setting pipeline to PAUSED ...
Pipeline is PREROLLED ...
Setting pipeline to PLAYING ...
New clock: GstSystemClock
Redistribute latency...
Redistribute latency...
FpsCounter(1sec): total=129.33 fps, number-streams=1, per-stream=129.33 fps
FpsCounter(1sec): total=128.22 fps, number-streams=1, per-stream=128.22 fps
0:00:26.1 / 0:00:53.9 (48.5 %)  C-c C-c^Chandling interrupt.
Interrupt: Stopping pipeline ...
Execution ended after 0:00:02.719796252
Setting pipeline to NULL ...
Freeing pipeline ...
```

Generating a configuration file via the run command.

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --measure density
```

Run standalone `gst-launch.sh`, with density configuration

Command:
```
./od-h264-ssd-mobilenet-v1-coco/measurements/density/dlstreamer/run-0000/iteration-0000/process-0000-stream-0000/density.gst-launch.sh
```

Example Output:
```
Setting pipeline to PAUSED ...
Pipeline is PREROLLED ...
Setting pipeline to PLAYING ...
New clock: GstSystemClock
Redistribute latency...
Redistribute latency...
FpsCounter(1sec): total=43.99 fps, number-streams=1, per-stream=43.99 fps
FpsCounter(1sec): total=42.86 fps, number-streams=1, per-stream=42.86 fps
0:00:08.1 / 0:00:53.9 (15.1 %)  C-c C-c^Chandling interrupt.
Interrupt: Stopping pipeline ...
Execution ended after 0:00:02.422359892
Setting pipeline to NULL ...
Freeing pipeline ...
```

