# Pipeline Runner Developer Guide

Pipeline runners implement media analytics pipelines based on tasks
defined in the pipeline zoo. Pipeline runners interact with
`pipebench` through a simple command line interface and configuration
file. Pipeline runners have one required and one optional argument.

## Command Line Interface
```
usage: piperun [-h] [--systeminfo SYSTEMINFO] piperun config

positional arguments:
  piperun config        piperun configuration file (.piperun.yml)

optional arguments:
  -h, --help            show this help message and exit
  --systeminfo SYSTEMINFO
```

## Piperun Configuration File

Pipeline runners are passed a yaml configuration file that specifies the
pipeline to run, inputs and outputs, and any runner specific
configuration. 

### Example
```yaml
%YAML 1.0
---
pipeline:
  task: object-detection
  model: yolo-v3-tf
  inputs.media.type.media-type: video/x-h264
inputs:
- uri: file:///home/pipeline-zoo/workspace/od-h264-yolov3/workloads/person-bicycle-car-detection/disk/input/stream.h264
  caps: video/x-h264
  extended-caps: video/x-h264, stream-format=(string)byte-stream, alignment=(string)au,
    level=(string)4, profile=(string)high, width=(int)1920, height=(int)1080, framerate=(fraction)24/1,
    pixel-aspect-ratio=(fraction)1/1, chroma-format=(string)4:2:0, bit-depth-luma=(uint)8,
    bit-depth-chroma=(uint)8, parsed=(boolean)true
  source: /home/pipeline-zoo/workspace/od-h264-yolov3/media/video/person-bicycle-car-detection/person-bicycle-car-detection_1920_1080_2min.mp4
outputs:
- uri: pipe:///tmp/5992d5c0-40b3-11ec-8e71-1c697a06fd65/output
  caps: metadata/objects,format=jsonl
runner-config:
  run: python3 dlstreamrun
  detect:
    inference-interval: 1
    device: CPU
models-root: /home/pipeline-zoo/workspace/od-h264-yolov3/models
pipeline-root: /home/pipeline-zoo/workspace/od-h264-yolov3
```
### Common Sections

#### pipeline

Provides details about the pipeline to run including the task and task
properties. Properties for a task are defined in the corresponding
`.task.yml` file but typically include input media types and models.

#### inputs

List of URIs to process including caps information (in `GStreamer` notation).

#### outputs

List of URIS of where to send output (one for each input URI). 

#### models-root

The root directory for models used in the pipeline.

#### pipeline-root

The root directory for the pipeline in the workspace.

#### runner-config

Runner specific configuration. 

Optionally includes `run` and `build` sections giving command lines
for building and running the pipeline runner.

Optionally includes `streams-per-process` key that dictates how many
streams to send to each invocation of a the pipeline runner. When
measuring stream density this controls how many processes will be
launched.

The rest of the options are runner specific and can include any
details required for a pipeline including platform specific
optimizations.

## Interaction with Pipebench

Pipebench generates configuration files for a specified workload and
passes those configuration files to a pipeline runner for execution.

Pipebench monitors execution and reports metrics such as FPS.

### Launching

Pipeline runners are launched with a working directory within the
workspace. By default all output is redirected to log files. 

### Input

Pipeline runners are passed URIs of input with coressponding media
type information in GStreamer caps format.


### Output

Pipeline runners are passed URIS of output with corresponding media
type information for what is exptected per frame.

#### ```metadata/objects,format=jsonl```

Indicates one line per frame with all inference results (detections plus classifications).

#### Example

```json
{"objects":[{"detection":{"bounding_box":{"x_max":0.09306159615516663,"x_min":0.06998172402381897,"y_max":0.9083143472671509,"y_min":0.8296394348144531},"confidence":0.8117787837982178,"label":"person","label_id":1},"h":85,"roi_type":"person","w":44,"x":134,"y":896},{"detection":{"bounding_box":{"x_max":0.845276951789856,"x_min":0.775219202041626,"y_max":0.8440243601799011,"y_min":0.7769706845283508},"confidence":0.8881521821022034,"label":"car","label_id":3},"h":72,"roi_type":"car","w":135,"x":1488,"y":839},{"detection":{"bounding_box":{"x_max":0.7463416457176208,"x_min":0.6845174431800842,"y_max":0.8342834711074829,"y_min":0.7789134979248047},"confidence":0.8703433871269226,"label":"car","label_id":3},"h":60,"roi_type":"car","w":119,"x":1314,"y":841},{"detection":{"bounding_box":{"x_max":0.4590078890323639,"x_min":0.3271484076976776,"y_max":0.8795638084411621,"y_min":0.7711740732192993},"confidence":0.7922513484954834,"label":"car","label_id":3},"h":117,"roi_type":"car","w":253,"x":628,"y":833},{"detection":{"bounding_box":{"x_max":0.6889902353286743,"x_min":0.6306229829788208,"y_max":0.8448697924613953,"y_min":0.7759309411048889},"confidence":0.7886551022529602,"label":"car","label_id":3},"h":74,"roi_type":"car","w":112,"x":1211,"y":838},{"detection":{"bounding_box":{"x_max":0.7855115532875061,"x_min":0.7429527640342712,"y_max":0.8322832584381104,"y_min":0.7805370092391968},"confidence":0.5301644802093506,"label":"car","label_id":3},"h":56,"roi_type":"car","w":82,"x":1426,"y":843},{"detection":{"bounding_box":{"x_max":0.9816077947616577,"x_min":0.9652698040008545,"y_max":0.6916195750236511,"y_min":0.6430597901344299},"confidence":0.6921101212501526,"label":"traffic light","label_id":10},"h":52,"roi_type":"traffic light","w":31,"x":1853,"y":695},{"detection":{"bounding_box":{"x_max":0.4307485520839691,"x_min":0.37247833609580994,"y_max":0.3871311843395233,"y_min":0.2757442891597748},"confidence":0.5129209756851196,"label":"traffic light","label_id":10},"h":120,"roi_type":"traffic light","w":112,"x":715,"y":298}],"resolution":{"height":1080,"width":1920},"timestamp":0}
{"objects":[{"detection":{"bounding_box":{"x_max":0.09381704032421112,"x_min":0.0695488303899765,"y_max":0.9087607264518738,"y_min":0.8254061341285706},"confidence":0.8358791470527649,"label":"person","label_id":1},"h":90,"roi_type":"person","w":47,"x":134,"y":891},{"detection":{"bounding_box":{"x_max":0.845042884349823,"x_min":0.7763723731040955,"y_max":0.8438907265663147,"y_min":0.776685893535614},"confidence":0.8921647071838379,"label":"car","label_id":3},"h":73,"roi_type":"car","w":132,"x":1491,"y":839},{"detection":{"bounding_box":{"x_max":0.7474825978279114,"x_min":0.6832204461097717,"y_max":0.8344070315361023,"y_min":0.7776212096214294},"confidence":0.8658412098884583,"label":"car","label_id":3},"h":61,"roi_type":"car","w":123,"x":1312,"y":840},{"detection":{"bounding_box":{"x_max":0.6879204511642456,"x_min":0.6289944648742676,"y_max":0.8436928391456604,"y_min":0.7752488255500793},"confidence":0.8031662702560425,"label":"car","label_id":3},"h":74,"roi_type":"car","w":113,"x":1208,"y":837},{"detection":{"bounding_box":{"x_max":0.4610901176929474,"x_min":0.3273378312587738,"y_max":0.8775742053985596,"y_min":0.77132248878479},"confidence":0.7843647599220276,"label":"car","label_id":3},"h":115,"roi_type":"car","w":257,"x":628,"y":833},{"detection":{"bounding_box":{"x_max":0.783437967300415,"x_min":0.7414575815200806,"y_max":0.83198082447052,"y_min":0.7799756526947021},"confidence":0.5148391723632813,"label":"car","label_id":3},"h":56,"roi_type":"car","w":81,"x":1424,"y":842},{"detection":{"bounding_box":{"x_max":0.9819191694259644,"x_min":0.9648196697235107,"y_max":0.6938728094100952,"y_min":0.6427075862884521},"confidence":0.7028929591178894,"label":"traffic light","label_id":10},"h":55,"roi_type":"traffic light","w":33,"x":1852,"y":694}],"resolution":{"height":1080,"width":1920},"timestamp":33333333}
```

#### ```metadata/line-per-frame,format=jsonl```

Indicates one line per frame (no results required). Newline should be
generated when frame processing is complete and all results are
available. If multiple inferences are required by the pipeline
definition than all results need to be received before a newline is
sent.

#### Example

```
{}
{}
```

### Measuring FPS

The FPS of a pipeline runner is measured by pipebench based on the
rate at which the output is generated. A frame is complete when a
newline is sent on the named pipe associated with the input stream. 

Example code for measuring FPS from a named pipe:

Media Sink:

https://github.com/intel-innersource/frameworks.ai.media-analytics.pipeline-zoo/blob/6bdf10ee8278722616128b89625643ef876423c8/tools/pipebench/pipebench/tasks/media_util.py#L305

Reading from Fifo:

https://github.com/intel-innersource/frameworks.ai.media-analytics.pipeline-zoo/blob/6bdf10ee8278722616128b89625643ef876423c8/tools/pipebench/pipebench/tasks/media_util.py#L390
