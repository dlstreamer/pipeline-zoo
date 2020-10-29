# Examples

## OpenCV-GAPI Runner

### Download object detection mobilenet ssd

```
pipebench download od-h264-mbnetssd
```
Output:
```
- od-h264-mbnetssd/
  + media/
  + models/
  - runners/
    + dlstreamer/
    + mockrun/
    - opencv-gapi/
      - gapirun/
        - build/
          + CMakeFiles/
          CMakeCache.txt
          Makefile
          cmake_install.cmake
          gapirun
        CMakeLists.txt
        arguments.hpp
        main.cpp
        postproc.hpp
        task.hpp
      + results/
      README.md
      build.sh
      packages.txt
  + workloads/
  README.md
  dlstreamer.config.yml
  media.list.yml
  mockrun.config.yml
  models.list.yml
  od-h264-mbnetssd.pipeline.yml
  opencv-gapi.config.yml
```

### Measure opencv-gapi runner
```
pipebench measure od-h264-mbnetssd --runner opencv-gapi
```
Output:
```
==============================
Ended: pipebench memory source
	Ended: 1603968962.1473718
	Frames Written: 4676
==============================

============================
Ended: pipebench memory sink
	Ended: 1603968962.1573753
	Frames Read: 4664
============================

pipeline          runner       media                                 avg FPS (selected)
----------------  -----------  ----------------------------------  --------------------
od-h264-mbnetssd  opencv-gapi  video/person-bicycle-car-detection               77.4712
```

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
