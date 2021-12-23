# Measurement Output

Measurement output files along with the commands used to create them
are stored in the pipeline workspace.

## Example output tree for `od-h264-mobilenet-ssd-v1-coco`

```
pipeline-zoo/workspace/od-h264-mobilenet-ssd-v1-coco/measurements
- density/
  - dlstreamer/
    - run-0000/
      - iteration-0000/
        - process-0000-stream-0000/
          density.gst-launch.sh
          density.piperun.yml
          stderr.txt
          stdout.txt
        - process-0001-stream-0001/
          density.gst-launch.sh
          density.piperun.yml
          stderr.txt
          stdout.txt
      density.measurement-settings.yml
      dlstreamer.runner-settings.yml
      systeminfo.json
	  result.json
- throughput/
  - dlstreamer/
    - run-0000/
      - iteration-0000/
        - process-0000-stream-0000/
          throughput.gst-launch.sh
          throughput.piperun.yml
      dlstreamer.runner-settings.yml
      systeminfo.json
      throughput.measurement-settings.yml
    + run-0001/
```

## Example `result.json`

```json
{
    "throughput": {
        "streams": 2,
        "max": 57.8524840451764,
        "min": 57.80778206933665,
        "avg": 57.83013305725653,
        "total": 115.66026611451306,
        "processes": 2,
        "iterations": {
            "Iteration: 0000": {
                "Stream: 0000": {
                    "avg": [
                        57.80778206933665,
                        true
                    ]
                },
                "Stream: 0001": {
                    "avg": [
                        57.8524840451764,
                        true
                    ]
                },
                "streams": 2,
                "max": 57.8524840451764,
                "min": 57.80778206933665,
                "avg": 57.83013305725653,
                "total": 115.66026611451306,
                "processes": 2
            }
        },
        "measurement_settings": {
            "media": "video/person-bicycle-car-detection",
            "streams": 2,
            "warm-up": 2,
            "duration": 60,
            "numactl": true,
            "target-fps": 30,
            "target-range": [
                0.2
            ],
            "target-condition": "total",
            "starting-streams": 0,
            "streams-per-process": 1,
            "max-processes": 0,
            "max-streams": 0,
            "max-iterations": 0,
            "min-streams": 1,
            "search-method": "linear",
            "sample-size": 30,
            "save-pipeline-output": false,
            "scenario": {
                "source": "disk",
                "type": "stream"
            },
            "use-reference-detections": false,
            "generate-reference": false
        },
        "runner_settings": {
            "run": "python3 dlstreamrun",
            "detect": {
                "device": "CPU",
                "precision": "FP32-INT8"
            },
            "decode": {
                "device": "CPU"
            },
            "streams-per-process": 1
        },
        "command_line": "/usr/local/bin/pipebench run od-h264-ssd-mobilenet-v1-coco --streams 2"
    }
}
```
