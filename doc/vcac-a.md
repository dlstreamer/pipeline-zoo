# Instructions for running on VCAC-A

Pipeline zoo currently supports version [VCAC-A_R5](https://github.com/OpenVisualCloud/VCAC-SW-Analytics/releases/tag/VCAC-A_R5) of the VCAC-A host and target software.
For instructions on setting up the VCAC-A please see Open Visual Cloud instructions: 
[VCAC-SW-Analytics](https://github.com/OpenVisualCloud/VCAC-SW-Analytics), [Dockerfiles/VCAC-A](https://github.com/OpenVisualCloud/Dockerfiles/tree/master/VCAC-A).

The following instructions assume that the host and target have been enabled and that the target's ip address is `172.32.1.1`.

## Build Pipeline Zoo Docker Environment for VCAC-A (on host)

On the host machine that is connected to the VCAC-A execute the following steps to build a Pipeline Zoo environment with VCAC-A support.

1. Clone Repo
   ```
   git clone https://gitlab.devtools.intel.com/media-analytics-pipeline-zoo/pipeline-zoo.git
   ```
2. Build Pipeline Zoo Environment
   ```
   ./pipeline-zoo/tools/docker/build.sh --platform vcac-a
   ```
   Output:
   ```
   Successfully built 113352079483
   Successfully tagged media-analytics-pipeline-zoo-bench-vcac-a:latest
   ```
3. Transfer Image to target
   ```
   docker save media-analytics-pipeline-zoo-vcac-a | ssh root@172.32.1.1 "docker load"
   ```
   Output:
   ```
   Loaded image: media-analytics-pipeline-zoo-vcac-a:latest
   ```
## Run Pipeline Zoo on VCAC-A Target

1. SSH to target.

   ```
   ssh root@172.32.1.1
   ```
2. Clone Repo
   ```
   git clone https://gitlab.devtools.intel.com/media-analytics-pipeline-zoo/pipeline-zoo.git
   ```
3. Start HDDL daemon
   ```
   /opt/intel/vcaa/vcaa_agent/run.sh start
   /opt/intel/vcaa/vpu_metric/run.sh start
   ps -aux | grep hddl

   ```
   Output:
   ```
   root     30500 14.4  0.3 2658824 23972 pts/0   Sl   07:15   0:26 /opt/intel/openvino_2020.2.120/deployment_tools/inference_engine/external/hddl/bin/hddldaemon
   root     30502  0.0  0.1 198460  8856 pts/0    Sl   07:15   0:00 /opt/intel/openvino_2020.2.120/deployment_tools/inference_engine/external/hddl/bin/autoboot --auxiliary
   ```
   
4. Launch Pipeline Zoo with VCAC-A environment
   ```
   ./pipeline-zoo/tools/docker/run.sh --platform vcac-a
   ```
5. Download Pipeline

   Command:
   ```
   pipebench download od-h264-mbnetssd
   ```

## Measure Pipeline Using VCAC-A configuration

Command:
     
 ```
       pipebench measure od-h264-mbnetssd --platform vcac-a --density
 ```
 
 
