# Example Commands for Intel(R) Core Platforms

> **Note:**
> These instructions assume that you have
> followed the [getting started guide](../README.md#getting-started) for cloning
> and building the Pipeline Zoo Environement.
>These instructions have been tested on [11th Gen Intel(R) Core(TM) i7-1185G7 Processor @ 3.00GHz](https://ark.intel.com/content/www/us/en/ark/products/208664/intel-core-i71185g7-processor-12m-cache-up-to-4-80-ghz-with-ipu.html). 
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
pipebench run od-h264-ssd-mobilenet-v1-coco --platform core
```

Example Output:

```
 Pipeline:
        od-h264-ssd-mobilenet-v1-coco

 Runner:
        dlstreamer
        dlstreamer.core.runner-settings.yml

 Media:
        video/person-bicycle-car-detection

 Measurement:
        throughput
        throughput.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/throughput/dlstreamer.core/run-0000

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
     0000      0001       0001   558.2964  558.2964  558.2964   558.2964
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   558.4061  558.4061  558.4061   558.4061
========================================================================

Pipeline                       Runner      Streams: 1
-----------------------------  ----------  ---------------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 558.4061 Max: 558.4061 Avg: 558.4061 Total: 558.4061

```

## Measure Stream Density
Command:

```
pipebench run od-h264-ssd-mobilenet-v1-coco --platform core --measure density
```

Example Output:
```
 Pipeline:
        od-h264-ssd-mobilenet-v1-coco

 Runner:
        dlstreamer
        dlstreamer.density.core.runner-settings.yml

 Media:
        video/person-bicycle-car-detection

 Measurement:
        density
        density.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/od-h264-ssd-mobilenet-v1-coco/measurements/density/dlstreamer.core/run-0000

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
      PRE      0000       0001     0.0000    0.0000    0.0000     0.0000
========================================================================

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0008      0011       0006    29.7477   29.9590   30.0731   329.5488
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0008      0011       0006    29.8048   29.9632   30.0719   329.5950
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0008      0011       0006    29.8430   29.9730   30.0530   329.7034
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0008      0011       0006    29.8457   29.9657   30.0693   329.6222
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0008      0011       0006    29.8482   29.9587   30.0682   329.5453
========================================================================

Pipeline                       Runner      Streams: 12                                             Streams: 11
-----------------------------  ----------  ------------------------------------------------------  ------------------------------------------------------
od-h264-ssd-mobilenet-v1-coco  dlstreamer  Min: 29.4417 Max: 30.0510 Avg: 29.9474 Total: 359.3691  Min: 29.8482 Max: 30.0682 Avg: 29.9587 Total: 329.5453


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
pipebench run oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf --platform core
```

Example Output:

```

 Pipeline:
        oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf

 Runner:
        dlstreamer
        dlstreamer.core.runner-settings.yml

 Media:
        video/person-bicycle-car-detection

 Measurement:
        throughput
        throughput.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf/measurements/throughput/dlstreamer.core/run-0000

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

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0001     0.0000    0.0000    0.0000     0.0000
========================================================================

<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   514.5576  514.5576  514.5576   514.5576
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   518.8857  518.8857  518.8857   518.8857
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   518.8857  518.8857  518.8857   518.8857
========================================================================

Pipeline                                    Runner      Streams: 1
------------------------------------------  ----------  ---------------------------------------------------------
oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf  dlstreamer  Min: 518.8857 Max: 518.8857 Avg: 518.8857 Total: 518.8857

```

## Measure Stream Density
Command:

```
pipebench run oc-h264-ssd-mobilenet-v1-coco-renset-50-tf --platform core --measure density
```

Example Output:
```
Pipeline:
        oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf

 Runner:
        dlstreamer
        dlstreamer.core.runner-settings.yml

 Media:
        video/person-bicycle-car-detection

 Measurement:
        throughput
        throughput.measurement-settings.yml

 Output Directory:
        /home/pipeline-zoo/workspace/oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf/measurements/throughput/dlstreamer.core/run-0000

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

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0000       0001     0.0000    0.0000    0.0000     0.0000
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   530.7611  530.7611  530.7611   530.7611
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0000      0001       0001   524.1402  524.1402  524.1402   524.1402
========================================================================
<SNIP>

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0003      0014       0007    30.0921   31.0048   32.1875   434.0669
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0003      0014       0007    30.1943   30.9869   32.1471   433.8162
========================================================================

========================================================================
Iteration   Streams  Processes    Minimum   Average   Maximum      Total
========================================================================
     0003      0014       0007    30.2541   30.9614   32.1082   433.4591
========================================================================

Pipeline                                    Runner      Streams: 15                                             Streams: 14
------------------------------------------  ----------  ------------------------------------------------------  ------------------------------------------------------
oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf  dlstreamer  Min: 22.5637 Max: 31.4325 Avg: 24.8456 Total: 372.6845  Min: 30.2541 Max: 32.1082 Avg: 30.9614 Total: 433.4591

```
