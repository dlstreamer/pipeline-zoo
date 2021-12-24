# Pipebench Reference Guide

The pipebench command line utility provides a single entrypoint for
interacting with pipelines. Using pipebench you can download a
pipeline along with its runners, sample media files and models. Once
downloaded you can use pipebench to measure the performance of a
pipeline under different scenarios.

## List

```
pipebench list -h
usage: pipebench list [-h] [-v] [--workspace WORKSPACE_ROOT]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbosity level (default: 0)
  --workspace WORKSPACE_ROOT
                        Workspace directory (default: .)
```

## Download
```
pipebench download -h
usage: pipebench download [-h] [-v] [--workspace WORKSPACE_ROOT] [--force] [--silent] pipeline

positional arguments:
  pipeline

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbosity level (default: 0)
  --workspace WORKSPACE_ROOT
                        Workspace directory (default: .)
  --force               Force download of existing pipeline (default: False)
  --silent              Disable output from download (default: False)
```

## Run

```
pipebench run -h
usage: pipebench run [-h] [-v] [--workspace WORKSPACE_ROOT] [--measure MEASUREMENT] [--runner RUNNER] [--runner-settings RUNNER_SETTINGS]
                     [--save-runner-settings SAVE_RUNNER_SETTINGS] [--platform PLATFORM] [--save-measurement-settings SAVE_MEASUREMENT_SETTINGS]
                     [--runner-override RUNNER_OVERRIDES RUNNER_OVERRIDES] [--measurement-settings MEASUREMENT_SETTINGS]
                     [--measurement-directory MEASUREMENT_DIRECTORY] [--force] [--media MEDIA] [--warm-up WARM_UP] [--duration DURATION]
                     [--numactl | --no-numactl] [--streams STREAMS] [--target-fps TARGET_FPS] [--target-condition {stream,average,total}]
                     [--sample-size SAMPLE_SIZE] [--target-range TARGET_RANGE] [--starting-streams STARTING_STREAMS]
                     [--streams-per-process STREAMS_PER_PROCESS] [--max-processes MAX_PROCESSES] [--max-streams MAX_STREAMS]
                     [--max-iterations MAX_ITERATIONS] [--min-streams MIN_STREAMS] [--search-method {linear,binary}] [--generate-reference]
                     [--save-pipeline-output]
                     pipeline

positional arguments:
  pipeline

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbosity level (default: 0)
  --workspace WORKSPACE_ROOT
                        Workspace directory (default: .)
  --measure MEASUREMENT
                        Measurement to perform. Used as selector for measurement and runner settings. (default: throughput)
  --runner RUNNER       Pipeline runner implementation (default: dlstreamer)
  --runner-settings RUNNER_SETTINGS
                        Pipeline runner settings. If not specified runner settings will be selected based on measurement and platform. (default:
                        None)
  --save-runner-settings SAVE_RUNNER_SETTINGS
                        Save pipeline runner settings with overrides. (default: None)
  --platform PLATFORM   Platform name. Used as selector for measurment and runner settings. (default: None)
  --save-measurement-settings SAVE_MEASUREMENT_SETTINGS
                        Name for saving measurement settings (default: None)
  --runner-override RUNNER_OVERRIDES RUNNER_OVERRIDES
                        Override settings for runner (default: [])
  --measurement-settings MEASUREMENT_SETTINGS
                        Measurement settings to load (default: None)
  --measurement-directory MEASUREMENT_DIRECTORY
                        Directory to store measurements (default: None)
  --force               Force clearing of previous results (default: False)

Measurement Settings:
  --media MEDIA         media name as listed in media.list.yml, path to media directory, or path to media file
  --warm-up WARM_UP     Number of samples to discard before reporting fps (default: 2)
  --duration DURATION   Number of seconds for run (default: 60)
  --numactl             Places each runner process on a numa node. Cycles between numa nodes so runner processes are distributed evenly accross
                        available nodes. (default: True)
  --no-numactl          Disable numactrl and use OS default placement
  --streams STREAMS     Number of concurrent media streams. If set to 0 (AUTO) pipebench will iterate until a maximum stream density is calculated
                        based on the target fps and target condition (default: 1)
  --target-fps TARGET_FPS
                        Target FPS (default: 30)
  --target-condition {stream,average,total}
                        Condition for selecting maximum during search. stream selects the maximum stream density with the requirement that each
                        individual stream meets the TARGET_FPS. average selects the maximum stream density with the requirement that the average FPS
                        over all streams meets the TARGET_FPS. total maximizes the total FPS (default: total)
  --sample-size SAMPLE_SIZE
                        Number of frames to use in updating FPS.Avg FPS will be recalculated every sample period. (default: 30)
  --target-range TARGET_RANGE
                        Min and max tolerance for target-fps as list [min,max]. [0] indicates target fps must be met (TARGET_FPS <= FPS). [0.2]
                        indicates (TARGET_FPS - 0.2) <= FPS. [0.2,0.2] indicates (TARGET_FPS - 0.2) <= FPS <= (TARGET_FPS + 0.2) (default: [0.2])
  --starting-streams STARTING_STREAMS
                        Number of concurrent media streams to start with when iterating to find maximum stream density. If set to 0 (AUTO) starting
                        streams will be calculated based on single process throughput / TARGET_FPS. Only applies when --streams is set to 0 (AUTO)
                        (default: 0)
  --streams-per-process STREAMS_PER_PROCESS
                        Number of media streams handled by each pipeline runner process. If set to 0 (NONE) all streams will be sent to a single
                        runner process. The number of pipeline runner processes launched in each iteration will be MIN( (NUMBER_OF_STREAMS /
                        STREAMS_PER_PROCESS), MAX_PROCESSES) (default: 1)
  --max-processes MAX_PROCESSES
                        Maximum number of pipeline runner processes to launch. If set to 0 (NO LIMIT) there is no limit and the number of processes
                        is determined by NUMBER_OF_STREAMS / STREAMS_PER_PROCESS. (default: 0)
  --max-streams MAX_STREAMS
                        Maximum number of concurrent media streams when iterating. If set to 0 (NO LIMIT) no limit is applied. Only applies when
                        --streams is set to 0 (AUTO). (default: 0)
  --max-iterations MAX_ITERATIONS
                        Maximum number of iterations to perform when finding maximum stream density. If set to 0 (NO LIMIT) no limit is applied. Only
                        applies when --streams is set to 0 (AUTO) (default: 0)
  --min-streams MIN_STREAMS
                        Minimum number of media streams when iterating. Must be less than or equal to--starting-streams (default: 1)
  --search-method {linear,binary}
                        Method for finding maximum stream density.Note: binary is experimental at this time. (default: linear)
  --generate-reference  Generate reference data when preparing workload.Note: Reference data is not needed for performance measurements and increases
                        workload preparation time significantly. (default: False)
  --save-pipeline-output
                        Save pipeline outputNote: Pipeline output is not needed for performance measurements and can impact FPS (default: False)
```
