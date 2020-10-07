'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import shlex
import subprocess
import shutil
from pipebench.util import create_directory
from pipebench.tasks.task import find_pipeline
from pipebench.schema.documents import validate
from pipebench.schema.documents import WorkloadConfig
from pipebench.schema.documents import PipelineConfig
import yaml
from collections import OrderedDict
import time
import math
import sys
from pipebench.tasks.media_util import FpsReport
from pipebench.util import print_action
import json
from pipebench.tasks.task import Task
from tabulate import tabulate

def measure(args):

    if (not args.workload):
        workload_path = "{}/default.workload.yml".format(args.workspace_root)
        with open(workload_path,
                  "w") as workload_file:
            minimal = "{measurement:{throughput:{}}}"
            if (args.density):
                minimal = "{measurement:{throughput:{},density:{}}}"
            workload_file.write(minimal)
        args.workload = workload_path
        
    workload = _load_workload(args)
    
    task = Task.create_task(workload, args)
    _prepare(task, workload, args)
    
    
    # load runner config
    
    runner_config_path = os.path.join(args.workspace_root,
                                      workload.pipeline,
                                      "{}.config.yml".format(args.runner))
    
    if ( (not os.path.isfile(runner_config_path)) and
         (os.path.isfile(runner_config_path.replace("yml","json")))):
        runner_config_path = runner_config_path.replace("yml","json")
    
    runner_config = validate(runner_config_path, args.schemas,args.runner_overrides)
    
    # create output folder for runner

    target_dir = os.path.join(args.pipeline_root,
                              "runners",
                              args.runner,
                              "results",
                              os.path.basename(args.workload_root))


    if (args.force):
        try:
            shutil.rmtree(target_dir)
        except Exception as error:
            pass

    if (not os.path.isdir(target_dir)):
        create_directory(target_dir)

    # write out workload file
    _write_workload(workload, target_dir, args) 

    previous_throughput = _read_existing_throughput(os.path.join(target_dir,"throughput"),args)

    if (args.density) and (previous_throughput) and (not args.throughput):
        throughput = previous_throughput
    elif ("throughput" in workload._document["measurement"]):
        throughput = _measure_throughput(task,
                                         workload,
                                         args,
                                         target_dir,
                                         runner_config)
        
    if ("density" in workload._document["measurement"]):
        density = _measure_density(throughput,
                                   task,
                                   workload,
                                   args,
                                   target_dir,
                                   runner_config)


def download(args):
    _download_pipeline(args.pipeline,
                      args)

def list_pipelines(args):

    descriptions = []
    for pipeline,pipeline_path in zip(args.pipelines[0],args.pipelines[1]):
        pipeline_config = PipelineConfig(pipeline_path,args)
        descriptions.append({"pipeline":pipeline,
                             "task":pipeline_config._namespace.task,
                             "model":pipeline_config._namespace.model})
    
    print(tabulate(descriptions,headers={'name':'name','model':'model','task':'task'},tablefmt="grid"))
    
def _create_download_command(pipeline, args):

    downloader = os.path.join(args.zoo_root,"tools/downloader/download")
    
    return shlex.split("python3 {0} -d {1} {2}".format(downloader,args.workspace_root,pipeline))

def _download_pipeline(pipeline, args):

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


def _create_systeminfo_command(target_dir, args):

    systeminfo = os.path.join(args.zoo_root,"tools/systeminfo/systeminfo")
    
    return shlex.split("python3 {0} -js {1}".format(systeminfo,os.path.join(target_dir,"systeminfo.json")))


def _load_workload(args):
    
    try:

        pipeline_path = find_pipeline(args.pipeline, args)

        if (not pipeline_path):
            args.parser.error("Pipeline {} not found in workspace".format(args.pipeline,))
       
        args.pipeline_root = os.path.dirname(pipeline_path)

        workload = WorkloadConfig(args.workload, args)
        workload_name = os.path.basename(args.workload)
        workload_name = workload_name.split('.')[0]

        args.workload_name = workload_name
        args.workload_root = os.path.join(args.
                                          workspace_root,
                                          workload.pipeline,
                                          "workloads",
                                          workload_name)

        
        return workload
    except Exception as error:
        args.parser.error("Invalid workload: {}, error: {}".format(args.workload,error))

    return None


def _prepare(task, workload, args):
            
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

    timeout = workload._namespace.measurement.throughput.duration
    if (not args.prepare_timeout):
        timeout = None
    task.prepare(args.workload_root, timeout)
    
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

def _write_density_result(density,
                          run_directory,
                          workload,
                          config,
                          results,
                          runner):
    
    iteration_results = {}
    stream_template = "Stream: {0:04d}"
    iteration_template="Iteration: {0:04d}"
    for iteration_index,result in enumerate(results):
        iteration_result = {}
        for stream_index,stream_result in enumerate(result):
            iteration_result[stream_template.format(stream_index)] = stream_result
        iteration_results[iteration_template.format(iteration_index)]=iteration_result
    
    result = {"density": {
        "streams":density,
        "iterations":iteration_results,
        "config":config
    }}

    result_file_name = os.path.join(run_directory,
                                    "result.json")

    with open(result_file_name,"w") as result_file:
        json.dump(result, result_file, indent=4)


    table = {'pipeline':workload.pipeline,
             'runner':runner,
             'media':workload._namespace.media,
             'density':density}
    
    headers = {key:key for key in table}
    print(tabulate([table],headers=headers))

    
def _write_throughput_result(run_directory,
                             workload,
                             config,
                             results,
                             runner):
    
    result = {"throughput": {
        "FPS":results,
        "config":config
    }}

    result_file_name = os.path.join(run_directory,
                                    "result.json")

    with open(result_file_name,"w") as result_file:
        json.dump(result, result_file, indent=4)

    table = {'pipeline':workload.pipeline,
             'runner':runner,
             'media':workload._namespace.media,
             '{}'.format(config["select"]):results[config["select"]]}
    headers = {key:key for key in table}
    headers[config["select"]]='{} FPS (selected)'.format(config["select"])
    print(tabulate([table],headers=headers))

def _normalize_range(config,range_name):
    if (not range_name in config):
        return None
    _min = config[range_name][0]
    _max = sys.maxsize
    if (len(config[range_name])>1):
        _max = config[range_name]
    return (_min,_max)

def _check_ranges(result, ranges):
    return {key:((getattr(result,key),(getattr(result,key)>=ranges[key][0] and getattr(result,key)<=ranges[key][1]))) for key in ranges if ranges[key]!=None}

def _check_density(results, config):
    success = True
    per_stream_results = results[0]
    ranges = {'min':_normalize_range(config,"minimum-range"),
              'avg':_normalize_range(config,"average-range")}
    range_results = [_check_ranges(stream_result,ranges) for stream_result in per_stream_results]
    for result in range_results:
        for key in result:
            if not result[key][1]:
                return False, range_results
    return True, range_results

def _print_density_result(range_results):
    stream_template = "Stream: {0:04d}"
    stream_results = []
    for index,range_result in enumerate(range_results):
        stream_results.append("{} {}".format(stream_template.format(index),
                                             " ".join(["{}:{}".format(key,value) for key,value in range_result.items()])))

    print_action("Density Result",stream_results)
                      
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

    results_directory = os.path.join(target_dir,
                                 "density")
    create_directory(results_directory)
    
    done = False
    density = 0
    first_result = None
    current_result = None
    iteration = 0
    iteration_results = []
    while (
            (first_result == current_result)
            and (num_streams>0) and (num_streams<=config["max-streams"])
    ):
        runners = []

        print_action("Stream Density",
                     ["Iteration: {}".format(iteration,),
                      "Number of Streams: {}".format(num_streams)])

        
        for stream_index in range(num_streams):

            run_directory = os.path.join(target_dir,
                                         "density",
                                         "iteration_{}".format(iteration),
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
        success, density_result =_check_density(results, config)
        _print_density_result(density_result)
        print_action("Stream Density",
                     ["Iteration: {}".format(iteration,),
                      "Number of Streams: {}".format(num_streams),
                      "Passed: {}".format(success)])
        iteration_results.append(density_result)
        if (first_result is None):
            first_result = success
        current_result = success
        if (success):
            if (density < num_streams):
                density = num_streams
            num_streams += 1
        else:
            num_streams -= 1
        iteration += 1

    _write_density_result(density,
                          os.path.join(target_dir,
                                       "density"),
                          workload,
                          config,
                          iteration_results,
                          args.runner)

def _read_existing_throughput(target_dir, args):
    path = os.path.join(target_dir,"result.json")
    if (os.path.isfile(path)):
        result = validate(os.path.join(target_dir,"result.json"),
                          args.schemas)
        if (result):
            return result["throughput"]["FPS"][result["throughput"]["config"]["select"]]
    return None
    
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

    _write_throughput_result(run_directory, workload, config, totals, args.runner)

    return totals[config['select']]
    

def _write_workload(workload, target_dir, args):

    workload_path = os.path.join(target_dir,
                                 os.path.basename(args.workload))
    
    with open(workload_path,"w") as workload_file:
        yaml.dump(workload._document,
                  workload_file,
                  sort_keys=False)
        
    
