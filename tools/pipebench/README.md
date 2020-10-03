# Pipebench

Pipebench will orchestrate the running of piplines as benchmarks

Controls Four Phases

1. Prepare
   * Prepare workloads 
   * Collect system info (using system info)
1. Run
   * Launch metrics collector
   * Launch pipeline impelementation 
   * Feed Data to pipeline
   * collect pipeline results
1. Check
   * Check accuracy
1. Report
   * Summarize FPS, Latency, System Metrics, Accuracy


Notes:

input directory contains encoded frames for task and scenario

input directory is specific to task and model and media

media / task / pipeline / input

media / task / pipeline / reference

video / task / pipeline / media / input

video / task / pipeline / media / reference 


Before running pipebench, assume:

pipeline directory
task specification

checks for and downloads:

 models
 media

Prepare:

 workspace/pipeline/media/media_name/scenario/input
 workspgace/pipeline/models/model
 
 workspace/pipeline/runner/config.yml



Pipeline Download:

 workspace/pipeline/media/media_name/
 workspace/pipeline/models/model/
 workspace/pipeline/runners/dlstreamer/config.yml


workspace is flat with pipelines





