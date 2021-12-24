# Example Commands for Intel(R) Xeon(R) Scalable Platforms

> **Note:**
> These instructions assume that you have
> followed the [getting started guide](../README.md#getting-started) for cloning
> and building the Pipeline Zoo Environement.
>These instructions have been tested on [Intel(R) Xeon(R) Gold 6336Y CPU @ 2.40GHz](https://ark.intel.com/content/www/us/en/ark/products/215280/intel-xeon-gold-6336y-processor-36m-cache-2-40-ghz.html). 
>
> Actual results will vary based on configuation and the examples below are for illustration purposes only.



# [Object Detection with ssd-mobilenet-v1-coco](../pipelines/video/object-detection/od-h264-ssd-mobilenet-v1-coco) 

## Download `od-h264-ssd-mobilenet-v1-coco`
Command:

```
pipebench download od-h264-ssd-mobilenet-v1-coco
```

Example Output:
```
=========================================
Downloading od-h264-ssd-mobilenet-v1-coco
=========================================


===================
Downloading Runners
===================

Download mockrun
Download dlstreamer

=================
Downloading Media
=================

Downloading: person-bicycle-car-detection.mp4
100%|████████████████████████████████████████████████████████████████████████████| 6.03M/6.03M [00:00<00:00, 68.4MiB/s]
Downloading: Pexels-Videos-1388365.mp4
100%|█████████████████████████████████████████████████████████████████████████████| 44.4M/44.4M [00:00<00:00, 109MiB/s]

==================
Downloading Models
==================

Download: ssd_mobilenet_v1_coco_INT8
Download: ssd_mobilenet_v1_coco

Pipeline Downloaded
```

## Measure Single Stream Throughput

Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --platform xeon
```

Example Output:

```
 Pipeline:
        od-h264-ssd-mobilenet-v1-coco

 Runner:
        dlstreamer
        dlstreamer.xeon.runner-settings.yml

 Media:
        video/person-bicycle-car-detection

 Measurement:
        throughput
        throughput.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer.xeon/run-0000

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   749.7203  749.7203  749.7203   749.7203
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   719.5014  719.5014  719.5014   719.5014
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   733.9822  733.9822  733.9822   733.9822
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   731.3879  731.3879  731.3879   731.3879
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   720.6601  720.6601  720.6601   720.6601
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   738.3210  738.3210  738.3210   738.3210
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   738.3210  738.3210  738.3210   738.3210
========================================================================

Pipeline                       Runner      Streams: 1
-----------------------------  ----------  ---------------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 738.3210 Max: 738.3210 Avg: 738.3210 Total: 738.3210
```

## Measure Stream Density
Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --platform xeon --measure density --starting-streams 120
```

Example Output:
```
 Pipeline:
        od-h264-ssd-mobilenet-v1-coco

 Runner:
        dlstreamer
        dlstreamer.density.xeon.runner-settings.yml

 Media:
        video/person-bicycle-car-detection

 Measurement:
        density
        density.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/density/dlstreamer.xeon/run-0007

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0120     0.0000    0.0000    0.0000     0.0000
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0006       0120     0.0000    3.2393  110.2287   388.7125
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0018       0120     0.0000   11.1226  113.0088  1334.7167
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0036       0120     0.0000   17.9127   82.5127  2149.5296
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0048       0120     0.0000   18.5534   63.8439  2226.4119
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0098       0120     0.0000   34.8576   55.8260  4182.9102
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0120       0120    24.4216   40.3254   51.4194  4839.0438
========================================================================

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0026      0146       0146    29.9917   31.1829   33.2088  4552.7030
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0026      0146       0146    29.9962   31.1636   33.1502  4549.8885
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0026      0146       0146    29.9803   31.1463   33.0965  4547.3558
========================================================================

```

# [Object Classification with resnet-50-tf](../pipelines/video/object-classification/oc-h264-ssd-mobilenet-v2-coco-resnet-50-tf)

## Download `oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf`
Command:

```
pipebench download oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf
```

Example Output:
```
======================================================
Downloading oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf
======================================================


===================
Downloading Runners
===================

Download dlstreamer
Download mockrun

=================
Downloading Media
=================

Downloading: person-bicycle-car-detection.mp4
100%|████████████████████████████████████████████████████████████████████████████| 6.03M/6.03M [00:00<00:00, 35.9MiB/s]
Downloading: Pexels-Videos-1388365.mp4
100%|█████████████████████████████████████████████████████████████████████████████| 44.4M/44.4M [00:00<00:00, 112MiB/s]

==================
Downloading Models
==================

Download: resnet-50-tf
Download: resnet-50-tf_INT8
Download: ssd_mobilenet_v1_coco_INT8
Download: ssd_mobilenet_v1_coco

Pipeline Downloaded
```

## Measure Single Stream Throughput

Command:

```
pipebench run oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf --platform xeon
```

Example Output:

```
Pipeline:
        oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf

 Runner:
        dlstreamer
        dlstreamer.xeon.runner-settings.yml

 Media:
        video/Pexels-Videos-1388365

 Measurement:
        throughput
        throughput.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf/measurements/throughput/dlstreamer.xeon/run-0000

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0001     0.0000    0.0000    0.0000     0.0000
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0001     0.0000    0.0000    0.0000     0.0000
========================================================================

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   112.6999  112.6999  112.6999   112.6999
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   112.7767  112.7767  112.7767   112.7767
========================================================================

Pipeline                                    Runner      Streams: 1
------------------------------------------  ----------  ---------------------------------------------------------
oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf  dlstreamer  Min: 112.7767 Max: 112.7767 Avg: 112.7767 Total: 112.7767


```

## Measure Stream Density
Command:

```
pipebench run oc-h264-ssd-mobilenet-v1-coco-renset-50-tf --platform xeon --measure density
```

Example Output:
```
 Pipeline:
        oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf

 Runner:
        dlstreamer
        dlstreamer.density.xeon.runner-settings.yml

 Media:
        video/Pexels-Videos-1388365

 Measurement:
        density
        density.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf/measurements/density/dlstreamer.xeon/run-0006

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
      PRE      0000       0001     0.0000    0.0000    0.0000     0.0000
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
      PRE      0000       0001     0.0000    0.0000    0.0000     0.0000
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
      PRE      0001       0001   202.3462  202.3462  202.3462   202.3462
========================================================================

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0001      0007       0007    29.0760   34.5873   43.0350   242.1114
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0001      0007       0007    29.0856   34.5848   43.0321   242.0933
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0001      0007       0007    29.0777   34.5968   43.1012   242.1777
========================================================================

Pipeline                                    Runner      Streams: 7                                              Streams: 6
------------------------------------------  ----------  ------------------------------------------------------  ------------------------------------------------------
oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf  dlstreamer  Min: 29.0777 Max: 43.1012 Avg: 34.5968 Total: 242.1777  Min: 35.0711 Max: 42.9154 Avg: 40.1244 Total: 240.7464

```
