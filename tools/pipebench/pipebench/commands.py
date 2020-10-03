'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import shlex
import subprocess
import shutil
from util import create_directory
from tasks.task import find_pipeline
from schema.documents import validate
import yaml
from collections import OrderedDict
import time
import math
import sys
from tasks.media_util import FpsReport
from util import print_action
import json

def _create_download_command(pipeline, args):

    downloader = os.path.join(args.zoo_root,"tools/downloader/download")
    
    return shlex.split("python3 {0} -d {1} {2}".format(downloader,args.workspace_root,pipeline))

def download_pipeline(pipeline, args):

    target_dir = os.path.join(args.workspace_root,pipeline)
    
    if (args.force):
        try:
            shutil.rmtree(target_dir)
        except Exception as error:
            pass

    if (not os.path.isdir(target_dir)):
        print("Pipeline not found in workspace, downloading")
                       
        command = _create_download_command(pipeline,args)

        subprocess.run(command)
    else:
        print("Pipeline found, skipping download")

def download(task, workload, args):
    
    download_pipeline(workload.pipeline,
                      args)

def _create_systeminfo_command(target_dir, args):

    systeminfo = os.path.join(args.zoo_root,"tools/systeminfo/systeminfo")
    
    return shlex.split("python3 {0} -js {1}".format(systeminfo,os.path.join(target_dir,"systeminfo.json")))

def prepare(task, workload, args):
    
        
    if (args.force):
        try:
            shutil.rmtree(args.workload_root)
        except Exception as error:
            pass

    if (not os.path.isdir(args.workload_root)):
        create_directory(args.workload_root)

        command = _create_systeminfo_command(args.workload_root,
                                             args)
    
        subprocess.run(command)


    directories = [os.path.join(args.workload_root,suffix) for suffix in ["input","reference"]]
                
    if (args.force):
        try:
            for directory in directories:
                shutil.rmtree(directory)
        except:
            pass

    for directory in directories:
        if (not os.path.isdir(directory)):
            create_directory(directory)

            
    task.prepare(args.workload_root)

def _print_fps(runners, totals):

    stream_stats = []

    totals.setdefault("total",-1)
    totals.setdefault("min",sys.maxsize)
    totals.setdefault("max",0)
    totals.setdefault("count",0)
    totals.setdefault("avg",0)
   
    total_fps = -1

    stream_template = "Stream: {index:04d}"

    template = "{stream} FPS:{stats.fps:04.4f} Min: {stats.min:04.4f} Max: {stats.max:04.4f} Avg: {stats.avg:04.4f}"
    output = []
    for index, (source, sink, runner_process) in enumerate(runners):
        if (source.is_alive()):
            
            stats = sink.get_fps()

            if (stats.min<sys.maxsize):
                total_fps += stats.fps
                output.append(template.format(stream=stream_template.format(index=index),
                                      stats=stats))
    if (len(runners) == 1):
        totals["total"] = stats.fps
        totals["min"] = stats.min
        totals["max"] = stats.max
        totals["avg"] = stats.avg
    elif ((total_fps > -1) and (len(output) == len(runners))):
        totals["total"]+=total_fps
        if (total_fps>=totals["max"]):
            totals["max"]=total_fps
        if (total_fps<=totals["min"]):
            totals["min"]=total_fps
        totals["count"]+=1
        totals["avg"] = totals["total"] / totals["count"]

        stats = FpsReport(total_fps,
                          totals["min"],
                          totals["max"],
                          0,
                          totals["avg"])
        
        output.append(template.format(stream="Total:      ",
                              stats=stats))
                          
    if (output):
        print_action("Frames Per Second", output)

def _wait_for_task(runners, duration):
    results = []
    start = time.time()
    totals = {}
    for (source, sink, runner_process) in runners:

        while((source.is_alive() and (not runner_process.poll()))
              and ((time.time()-start) < duration)):
            source.join(1)
            _print_fps(runners, totals)
           
        if (source.connected):
            source.stop()
            source.join()
        
        runner_process.kill()

        if (sink.connected):
            sink.stop()
            sink.join()
        results.append(sink.get_fps())
    if ("total" in totals):
        del totals["total"]
    return results, totals

def _write_throughput_result(run_directory,
                             workload,
                             config,
                             results):
    
    result = {"throughput": {
        "FPS":results,
        "config":config
    }}

    result_file_name = os.path.join(run_directory,
                                    "result.json")

    with open(result_file_name,"w") as result_file:
        json.dump(result, result_file, indent=4)
    print(result_file_name)
    
    print(result)

def _report_throughtput(run_directory,
                        workload,
                        config,
                        results):
    pass
    # report = {"throughput": {
    #     "max":
    #     "min":
    #     "avg":
    #     "select": {
    #         "min": 
    #         }
    # }
    # }
    
    
#    report_file_name = os.path.join(run_directory,
 #                                   "throughput.json")
    
def _measure_density(throughput,
                     task,
                     workload,
                     args,
                     target_dir,
                     runner_config):
    
    config = workload._document["measurement"].get("density",{})

    # now run with that many streams lower bound

    num_streams = min(config["max-streams"],math.floor(throughput / workload._document["measurement"]["density"]["fps"]))

    print_action("Measuring Stream Density",[config])
    
    runners = []
            
    for stream_index in range(num_streams):

        run_directory = os.path.join(target_dir,
                                     "density",
                                     "stream_{}".format(stream_index))
        create_directory(run_directory)

        source, sink, runner  = task.run(run_directory,
                                         runner_config,
                                         config["warm-up"],
                                         config["fps"],
                                         config["sample-size"])
        

        time.sleep(2)

        runners.append((source,sink,runner))
    
    results = _wait_for_task(runners, config["duration"])
    

def _measure_throughput(task,
                        workload,
                        args,
                        target_dir,
                        runner_config):
  
    run_directory = os.path.join(target_dir,
                                 "throughput")
    create_directory(run_directory)

    config = workload._document["measurement"].get("throughput", {})
    print_action("Measuring Throughput",[config])
    source, sink, runner = task.run(run_directory,
                                    runner_config,
                                    config["warm-up"],
                                    -1,
                                    config["sample-size"])

    per_stream_results, totals = _wait_for_task([(source, sink, runner)],

                                                config["duration"])

    _write_throughput_result(run_directory, workload, config, totals)

    return totals[config['select']]
    

def _write_workload(workload, args):

    workload_path = os.path.join(args.workload_root,
                                 os.path.basename(args.workload))
    
    with open(workload_path,"w") as workload_file:
        yaml.dump(workload._document,
                  workload_file,
                  sort_keys=False)
        
    
def run(task, workload, args):

    # write out workload file
    _write_workload(workload, args) 
    
    # load runner config
    
    runner_config_path = os.path.join(args.workspace_root,
                                 workload.pipeline,
                                 "{}.config.yml".format(args.runner))

    if (not os.path.isfile(runner_config_path)) and (os.path.isfile(runner_config_path.replace("yml","json"))):
        runner_config_path = runner_config_path.replace("yml","json")

    runner_config = validate(runner_config_path, args.schemas)
    
    # create output folder for runner

    target_dir = os.path.join(args.workload_root,
                              "results",
                              args.runner)

    if (args.force):
        try:
            shutil.rmtree(target_dir)
        except Exception as error:
            pass

    if (not os.path.isdir(target_dir)):
        create_directory(target_dir)

        
    throughput = _measure_throughput(task,
                                     workload,
                                     args,
                                     target_dir,
                                     runner_config)


    density = _measure_density(throughput,
                               task,
                               workload,
                               args,
                               target_dir,
                               runner_config)
    exit(1)
        

        
    

def view(task, workload, args):
    pass

def report(task, workload, args):
    pass


command_map = {
    'download':download,
    'prepare':prepare,
    'run':run,
    'view':view,
    'report':report
}
