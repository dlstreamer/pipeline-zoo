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
