# Examples

## Fixed number of streams at 30 FPS
```
pipebench measure od-h264-mbnetssd --density --override measurement.density.fixed-streams 2
```
Output:
```
==============
Density Result
	Stream: 0000 avg:(29.552433280067127, True)
	Stream: 0001 avg:(29.558242452568567, True)
==============

==============
Stream Density
	Iteration: 0
	Number of Streams: 2
	Passed: True
==============

pipeline          runner      media                                 density
----------------  ----------  ----------------------------------  ---------
od-h264-mbnetssd  dlstreamer  video/person-bicycle-car-detection          2
```

## Fixed number of streams at max FPS
```
pipebench measure od-h264-mbnetssd --density --override measurement.density.fixed-streams 2 --override measurement.density.fps -1
```
Output:
```
==============
Density Result
	Stream: 0000 avg:(56.73420837320125, True)
	Stream: 0001 avg:(53.971622574419364, True)
==============

==============
Stream Density
	Iteration: 0
	Number of Streams: 2
	Passed: True
==============

pipeline          runner      media                                 density
----------------  ----------  ----------------------------------  ---------
od-h264-mbnetssd  dlstreamer  video/person-bicycle-car-detection          2
```

## Running Standalone gst-launch

Generating a configuration file via the measure command.

```
pipebench measure od-h264-mbnetssd --density
```

Run standalone `gst-launch.sh`, with throughput configuration
```
./od-h264-mbnetssd/measurements/person-bicycle-car-detection/throughput/dlstreamer/person-bicycle-car-detection.gst-launch.sh
```

Run standalone `gst-launch.sh`, with density configuration

```
./od-h264-mbnetssd/measurements/person-bicycle-car-detection/density.30fps/dlstreamer/iteration_0/stream_0/person-bicycle-car-detection.gst-launch.sh
```

## Adding timestamp to measurements

```
pipebench measure od-h264-mbnetssd --density --add-timestamp
```

Output:

```
od-h264-mbnetssd/measurements/person-bicycle-car-detection_1605023001
```

## Saving Runner Overrides
```
pipebench measure od-h264-mbnetssd --runner-override detect.nireq 100 --save-runner-config 100_nireq
```

Output:
```
od-h264-mbnetssd/dlstreamer.100_nireq.config.yml
```

## Running Saved Overrides

```
pipebench measure od-h264-mbnetssd --runner-override detect.nireq 100 --runner-config 100_nireq
```

## Starting Stream Density Iteration
```
pipebench measure od-h264-mbnetssd --density --override measurement.density.starting-streams 10
```

## Saving Measurement Overrides
```
pipebench measure od-h264-mbnetssd --density --override measurement.density.duration 300 --override measurement.density.fixed-streams 10 --save-workload 5min
```

Output:

```
od-h264-mbnetssd/measurements/5min
```

## running Measurment Overrides
```
pipebench measure od-h264-mbnetssd --density --workload od-h264-mbnetssd/measurements/5min/5min.workload.yml
```
