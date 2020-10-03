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
                          redirect=True):

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

    runner_command.extend(["--systeminfo", systeminfo_path])

    runner_command.append(piperun_config_path)

    start_time = time.time()

    util.print_action("Launching: {}".format(runner),
                      ["Started: {}".format(start_time),
                       "Command: {}".format(runner_command)])
    process = subprocess.Popen(runner_command,
                               cwd=runner_root,
                               stdout=stdout_file,
                               stderr=stderr_file)
    return process

#    print (args.workload_root)
    pass

#def start_pipeline_runner(runner, piperun_config_path, args):
 #   runner_config = os.path.join(args.pipeline_root, runner)
    
#    def validate(document_path, schema_store):
    
    pass

def stop_pipeline_runner():
    pass
