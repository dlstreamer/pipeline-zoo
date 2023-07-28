
# How to Run Media Analytics (MA) Performance Measurements for Intel® Data Center GPU Flex Series

## 1. Install Required Software on Host machine
* Get your system ready to run media analytics workloads with Intel GPU, follow instructions here. 
https://dgpu-docs.intel.com/installation-guides/ubuntu/ubuntu-jammy-dc.html
* Install other required tools
```bash
sudo apt install -y  python3-pip linux-tools-common linux-tools-generic sysstat clinfo
pip install XlsxWriter
```
* Enable performance mode
```bash
sudo /usr/lib/linux-tools-<version>/cpupower frequency-set --governor performance
```

_***NOTE***_: Before running performance measurement of media analytics pipeline, its output needs to be checked to confirm it is producing expected result. For more information how to check pipeline output see [Intel® Deep Learning Streamer Pipeline Framework Metadata Publishing](https://github.com/dlstreamer/dlstreamer/tree/master/samples/gstreamer/gst_launch/metapublish)
## 2. Build Pipeline Zoo
```bash
git clone https://github.com/dlstreamer/pipeline-zoo.git
cd pipeline-zoo
./tools/docker/build.sh --platform dgpu --pipeline-list tools/docker/assets/dgpu-ma-pipelines.yml --tag dlstreamer-pipeline-zoo-dgpu
```
## 3. Run Pipeline Zoo
```bash
./tools/docker/run.sh --platform dgpu --mount-src false --user root -v /home/$USER/.netrc:/root/.netrc --image dlstreamer-pipeline-zoo-dgpu --name dlstreamer-pipeline-zoo-dgpu
```

## 4. Measure Performance 
| Short Name | Detailed Name | Pipebench pipeline name |
|------------|------------------------------| ------------------------- |
| AVC OD | ObjDet. AVC+MobileNet (1 Inf/Fr) bs=64 | od-h264-ssd-mobilenet-v1-coco |
| HEVC OD | ObjDet. HEVC+MobileNet (1 Inf/Fr) bs=64 | od-h265-ssd-mobilenet-v1-coco |
| AVC OC | ObjClass. AVC + Resnet50 (1 Inf/Fr)  bs=64 | oc-h264-full_frame-resnet-50-tf  |
| HEVC OC | ObjClass. HEVC + Resnet50 (1 Inf/Fr)  bs=64 | oc-h265-full_frame-resnet-50-tf  |
| AVC OD+OC | ObjDet&Class. AVC +MobileNet+RN50 (1 Inf/Fr) bs=64 | oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf |
| HEVC OD+OC | ObjDet&Class. HEVC+MobileNet+RN50 (1 Inf/Fr) bs=64 | oc-h265-ssd-mobilenet-v1-coco-resnet-50-tf |

* Below Commands are for system with single GPU card, for two GPU cards, change `--streams 8` to `--streams 16`.
* Commands are set to run for duration 10 minutes with flag `--duration 600`.

| Name| Command|
|----------|------------------|
| AVC OD | `pipebench run --measure density --force --platform dgpu od-h264-ssd-mobilenet-v1-coco --media video/20200711_dog_bark-1080p --no-numactl --duration 600 --streams 8 --streams-per-process 8`  |
| HEVC OD | `pipebench run --measure density --force --platform dgpu od-h265-ssd-mobilenet-v1-coco --media video/20200711_dog_bark-1080p-h265 --no-numactl --duration 600 --streams 8 --streams-per-process 8` |
| AVC OC | `pipebench run --measure density --force --platform dgpu oc-h264-full_frame-resnet-50-tf --media  video/20200711_dog_bark-1080p --no-numactl --duration 600 --streams 8 --streams-per-process 8` |
| HEVC OC | `pipebench run --measure density --force --platform dgpu oc-h265-full_frame-resnet-50-tf --media video/20200711_dog_bark-1080p-h265 --no-numactl --duration 600 --streams 8 --streams-per-process 8` |
| AVC OD+OC | `pipebench run --measure density --force --platform dgpu oc-h264-ssd-mobilenet-v1-coco-resnet-50-tf --media  video/20200711_dog_bark-1080p --no-numactl --duration 600 --streams 8 --streams-per-process 8` |
| HEVC OD+OC | `pipebench run --measure density --force --platform dgpu oc-h265-ssd-mobilenet-v1-coco-resnet-50-tf --media video/20200711_dog_bark-1080p-h265 --no-numactl --duration 600 --streams 8 --streams-per-process 8` |


## Notes on MA Performance Measurements for Intel® Data Center GPU Flex Series

It is normal to have some variance between any two SoCs of the same design and the same manufacturing process. Tiny unavoidable differences change the amount of leakage current in each chip.  Usually this variance is negligible, but it can manifest as performance differences under identical power limits.  This is more noticeable at higher operating temperatures. You may see some small performance differences between GPUs under identical operating conditions.  

In general, as temperature increases peak performance decreases.  As temperatures rise, leakage current increases, and power management must lower the voltage to stay within designed power limits.  Lower voltage means lower clock speeds, which will directly translate to lower performance.   

These GPUs do not have active cooling fans, so you must ensure that your server is set up with proper airflow to the GPUs. Performance is measured after starting from idle state and running for ~1-2 minutes. With room temperature ambient air and proper airflow, the GPUs will heat up to 55-60 C range after ~1-2 minutes.    

In addition to temperature impacts, the voltage and clock frequency will change depending on the utilization of the media engines and compute engines at any given time.  In Intel® Data Center GPU Flex Series, the media engines and compute engine share a GPU clock but have different voltage and frequency needs/limits. Therefore, changing the ratio of media engine utilization vs. compute engine utilization can significantly change the clock speed and end-to-end performance.

The media engine and compute engine utilization can change depending on batch size, input video details (codec, resolution, bitrate, etc.), the inference models used, the number of objects in the video content to be detected/classified, etc.  To reproduce the results make sure to follow the instructions, use the exact command lines, and input video provided.

## Intel® XPU Manager tool

To profile GPU resource utilizations, temperature, frequency, and other telemetry you could use Intel® XPU Manager, see [Intel® XPU Manager](https://github.com/intel/xpumanager).