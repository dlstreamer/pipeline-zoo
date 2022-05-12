# Examples

## Viewing gst-launch command output corresponding to measurement

The command used to launch a Pipeline Runner along with its output is stored in the 
workspace measurment folder: 

`workspace/<pipeline>/measurements/<measurement>/<run-N>/<iteration-N>/process-0000-stream-0000/stdout.txt`

To see the output directly on the console use the verbose setting `-vv`.

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

## Running standalone gst-launch

The corresponding standalone Pipeline Runner command is stored in the measurements folder. 

For Intel® Deep Learning Streamer (Intel® DL Streamer) Pipeline Framework this is a shell script with a `gst-launch` string:

```./od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0000/iteration-0000/process-0000-stream-0000/throughput.gst-launch.sh```

### Running standalone gst-launch with throughput settings

Generate script with run command.

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco 
```

Run standalone `gst-launch.sh`, with throughput settings

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

### Running standalone gst-launch with density settings

Generate script with run command.

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --measure density
```

Run standalone `gst-launch.sh`, with density settings

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

## Overriding Pipeline Runner Settings

Pipeline runner settings an be overriden on the command line by using the `runner-override` argument.
`runner-override` takes a key and value pair.

### Changing inference interval for Intel® DL Streamer Pipeline Runner

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --runner-override detect.inference-interval 3 -vv
```

Example Output:
```
=======================
Arguments for pipebench
=======================
	command == <function run at 0x7f4b04cd0430>
	verbose_level == 2
	workspace_root == .
	pipeline == od-h264-ssd-mobilenet-v1-coco
	measurement == throughput
	runner == dlstreamer
	runner_settings == None
	save_runner_settings == None
	platform == None
	save_measurement_settings == None
	runner_overrides == [['detect.inference-interval', '3']]
	measurement_settings == None
	measurement_directory == None
	force == False


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
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0002

=====================
Launching: dlstreamer
	Started: 1640349961.4792063
	Command: ['numactl', '--cpunodebind', '0', '--membind', '0', 'python3', 'dlstreamrun', '--systeminfo=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/systeminfo.json', '/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0002/iteration-0000/process-0000-stream-0000/throughput.piperun.yml']
=====================

=========================
Arguments for dlstreamrun
=========================
	systeminfo == /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/systeminfo.json
	piperun_config == /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0002/iteration-0000/process-0000-stream-0000/throughput.piperun.yml


No FP32-INT8 Model found, trying: FP32

gst-launch-1.0 filesrc location=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/input/stream.fps.mp4 ! qtdemux ! h264parse ! video/x-h264 ! avdec_h264 name=decode0 ! gvadetect device=CPU inference-interval=3 name=detect0 model-proc=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco_INT8/FP16-INT8/ssd_mobilenet_v1_coco_INT8.json model=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco/FP32/ssd_mobilenet_v1_coco.xml ! gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/731dd27e-64b7-11ec-a730-1c697a06fd65/output ! gvafpscounter ! fakesink async=false name=sink0
```

### Changing device for Intel® DL Streamer Pipeline Runner

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --runner-override detect.device GPU -vv
```

Example Output:

```
=======================
Arguments for pipebench
=======================
	command == <function run at 0x7fcaa8fc5430>
	verbose_level == 2
	workspace_root == .
	pipeline == od-h264-ssd-mobilenet-v1-coco
	measurement == throughput
	runner == dlstreamer
	runner_settings == None
	save_runner_settings == None
	platform == None
	save_measurement_settings == None
	runner_overrides == [['detect.device', 'GPU']]
	measurement_settings == None
	measurement_directory == None
	force == False


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
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0003

=====================
Launching: dlstreamer
	Started: 1640350193.4521034
	Command: ['numactl', '--cpunodebind', '0', '--membind', '0', 'python3', 'dlstreamrun', '--systeminfo=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/systeminfo.json', '/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0003/iteration-0000/process-0000-stream-0000/throughput.piperun.yml']
=====================

=========================
Arguments for dlstreamrun
=========================
	systeminfo == /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/systeminfo.json
	piperun_config == /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0003/iteration-0000/process-0000-stream-0000/throughput.piperun.yml


No FP32-INT8 Model found, trying: FP32

gst-launch-1.0 filesrc location=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/.workloads/person-bicycle-car-detection/disk/input/stream.fps.mp4 ! qtdemux ! h264parse ! video/x-h264 ! avdec_h264 name=decode0 ! gvadetect device=GPU name=detect0 model-proc=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco_INT8/FP16-INT8/ssd_mobilenet_v1_coco_INT8.json model=/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/models/ssd_mobilenet_v1_coco/FP32/ssd_mobilenet_v1_coco.xml ! gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/fd621846-64b7-11ec-b8e0-1c697a06fd65/output ! gvafpscounter ! fakesink async=false name=sink0
```

## Overriding Measurement Settings

### Changing duration of runs

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --duration 10
```

Example Output:
```
pipebench run od-h264-ssd-mobilenet-v1-coco --duration 10

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
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer/run-0004

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0001     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   128.9480  128.9480  128.9480   128.9480
======================================================================== 

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   130.2250  130.2250  130.2250   130.2250
======================================================================== 

Pipeline                       Runner      Streams: 1
-----------------------------  ----------  ---------------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 130.2250 Max: 130.2250 Avg: 130.2250 Total: 130.2250
```

### Runing fixed number of streams

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --streams 2
```

Example Output:
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
### Changing target fps

```
pipebench run od-h264-ssd-mobilenet-v1-coco --target-fps 10 --measure density
```

Example Output:

```
 Pipeline:
	od-h264-ssd-mobilenet-v1-coco

 Runner:
	dlstreamer
 	dlstreamer.density.runner-settings.yml

 Media:
	video/person-bicycle-car-detection

 Measurement:
	density
 	density.measurement-settings.yml

 Output Directory:
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/density/dlstreamer/run-0001

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
      PRE      0001       0001   132.9510  132.9510  132.9510   132.9510
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
      PRE      0001       0001   129.6087  129.6087  129.6087   129.6087
======================================================================== 

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0002      0011       0011     9.9835   10.0543   10.1575   110.5978
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0002      0011       0011     9.9835   10.0543   10.1575   110.5978
======================================================================== 

Pipeline                       Runner      Streams: 12                                          Streams: 11
-----------------------------  ----------  ---------------------------------------------------  -----------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 8.6523 Max: 9.8086 Avg: 9.2225 Total: 110.6702  Min: 9.9835 Max: 10.1575 Avg: 10.0543 Total: 110.5978
```

## Storing and reusing measurement settings

Changes to measurement settings can be stored and named as a new type
of measurement.  For example, to save a new measurement called:
`density-10` with a `target-fps` of 10 you can use the following
commands.

Command:
```
pipebench run od-h264-ssd-mobilenet-v1-coco --target-fps 10 --measure density --save-measurement-settings density-10
```

To rerun the measurement with the new settings pass it to the `--measurement-settings` argument.

Command:
```
pipebench run od-h264-ssd-mobilenet-v1-coco --measure density --measurement-settings density-10
```

Example Output:
```
 Pipeline:
	od-h264-ssd-mobilenet-v1-coco

 Runner:
	dlstreamer
 	dlstreamer.density.runner-settings.yml

 Media:
	video/person-bicycle-car-detection

 Measurement:
	density
 	density-10.measurement-settings.yml

 Output Directory:
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/density/dlstreamer/run-0003

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
      PRE      0001       0001   133.1901  133.1901  133.1901   133.1901
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
      PRE      0001       0001   130.6435  130.6435  130.6435   130.6435
======================================================================== 

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0002      0011       0011     9.9835   10.0543   10.1575   110.5978
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0002      0011       0011     9.9835   10.0543   10.1575   110.5978
======================================================================== 

Pipeline                       Runner      Streams: 12                                          Streams: 11
-----------------------------  ----------  ---------------------------------------------------  -----------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 8.6523 Max: 9.8086 Avg: 9.2225 Total: 110.6702  Min: 9.9835 Max: 10.1575 Avg: 10.0543 Total: 110.5978
```
## Storing and reusing Pipeline Runner settings

Changes to pipeline runner settings can be stored and named.  For example, to save a new runner setting called:
`interval-3` with a `detect.inference-interval` of `3` you can use the following commands.

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --save-runner-settings interval-3 --runner-override detect.inference-interval 3 --measure density
```

To rerun the measurement with the new settings pass it to the `--runner-settings` argument.

Command:
```
pipebench run od-h264-ssd-mobilenet-v1-coco --runner-settings interval-3 --measure density --starting-streams 10
```

Example Output:
```
 Pipeline:
	od-h264-ssd-mobilenet-v1-coco

 Runner:
	dlstreamer
 	dlstreamer.interval-3.runner-settings.yml

 Media:
	video/person-bicycle-car-detection

 Measurement:
	density
 	density.measurement-settings.yml

 Output Directory:
	/home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/density/dlstreamer.interval-3/run-0004

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0010     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0010     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0010     0.0000    0.0000    0.0000     0.0000
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0010       0010    29.8353   29.9821   30.0405   299.8210
======================================================================== 

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0001      0011       0011    27.0034   28.9120   30.1269   318.0325
======================================================================== 

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0001      0011       0011    27.1203   28.9225   30.1359   318.1471
======================================================================== 

Pipeline                       Runner      Streams: 11                                             Streams: 10
-----------------------------  ----------  ------------------------------------------------------  ------------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 27.1203 Max: 30.1359 Avg: 28.9225 Total: 318.1471  Min: 29.9964 Max: 30.0001 Avg: 29.9996 Total: 299.9963

```
