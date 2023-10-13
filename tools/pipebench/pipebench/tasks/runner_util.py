import subprocess
import os
from pipebench.schema.documents import validate
import shlex
import util
import time

def start_pipeline_runner(runner,
                          runner_config,
                          run_root,
                          piperun_config_path,
                          pipeline_root,
                          systeminfo_path,
                          redirect=True,
                          numa_node = None,
                          gpu_render_device = None,
                          verbose_level=0):

    runner_root = os.path.join(pipeline_root, "runners", runner)

    default_run = os.path.join(runner_root, "run.sh")


    if (redirect):
        stdout_path = os.path.join(run_root, "stdout.txt")

        stderr_path = os.path.join(run_root, "stderr.txt")

        stdout_file = open(stdout_path,"w")

        stderr_file = open(stderr_path,"w")
    else:
        stdout_file = None
        stderr_file = None

    if (runner_config and "run" in runner_config):
        runner_command = shlex.split(runner_config["run"])
    else:
        runner_command = ["/bin/bash",default_run]

    runner_command.extend(["--systeminfo={}".format(systeminfo_path)])

    runner_command.append(piperun_config_path)
    if numa_node is not None:
        runner_command = ["numactl","--cpunodebind",str(numa_node),"--membind",str(numa_node)] + runner_command

    environment = None
    render_device_verbose = []

    # Do not set environment if already set by docker/run.sh
    if gpu_render_device is not None and "GST_VAAPI_DRM_DEVICE" not in os.environ:
        environment = dict(os.environ,GST_VAAPI_DRM_DEVICE=gpu_render_device)
        render_device_verbose = ["GST_VAAPI_DRM_DEVICE: {}".format(gpu_render_device)]
        util.print_action("Setting GST_VAAPI_DRM_DEVICE to {}".format(gpu_render_device))

    if "latency" in runner_config:
        latency_log = os.path.join(
            run_root, runner_config["latency"]["GST_DEBUG_FILE"])
        util.print_action("Latency file {}\n".format(latency_log))
        runner_config["latency"].update({"GST_DEBUG_FILE": latency_log})
        environment = dict(os.environ, **runner_config["latency"])

    start_time = time.time()
    if verbose_level>0:
        util.print_action("Launching: {}".format(runner),
                          ["Started: {}".format(start_time),
                           "Command: {}".format(runner_command)]+
                          render_device_verbose)


    process = subprocess.Popen(runner_command,
                               cwd=runner_root,
                               stdout=stdout_file,
                               stderr=stderr_file,
                               env=environment)
    return process

