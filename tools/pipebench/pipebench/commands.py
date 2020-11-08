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
from pipebench.schema.documents import apply_overrides
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
import tempfile
from statistics import mean

def measure(args):

    if (not args.workload):
        with tempfile.TemporaryDirectory() as workload_root:
            workload_path = "{}/workload.yml".format(workload_root)
            with open(workload_path,
                      "w") as workload_file:
                minimal = "{measurement:{throughput:{}}}"
                if (args.density):
                    minimal = "{measurement:{throughput:{},density:{}}}"
                workload_file.write(minimal)
            args.workload = workload_path
            workload = _load_workload(args)
    else:
        workload = _load_workload(args)
    task = Task.create_task(workload, args)
    _prepare(task, workload, args)
    
    
    # load runner config
    
    runner_config_path = os.path.join(args.workspace_root,
                                      workload.pipeline,
                                      "{}{}.config.yml".format(args.runner,
                                                               ".{}".format(args.runner_config) if args.runner_config else ""))
    
    if ( (not os.path.isfile(runner_config_path)) and
         (os.path.isfile(runner_config_path.replace("yml","json")))):
        runner_config_path = runner_config_path.replace("yml","json")
        
    # create output folder for runner

    measurements = ["throughput"]

    if ("density" in workload._document["measurement"]):
        measurements.append("density.{}fps".format(workload._namespace.measurement.density.fps))
    
    target_dirs = [ os.path.join(args.pipeline_root,
                                 "measurements",
                                 args.workload_name,
                                 measurement,
                                 os.path.basename(runner_config_path).replace(".config.yml","").replace(".config.json",""))
                    for measurement in measurements]


    if (args.force):
        try:
            for target_dir in target_dirs:
                shutil.rmtree(target_dir)
        except Exception as error:
            pass
        
    for target_dir in target_dirs:
        if (not os.path.isdir(target_dir)):
            create_directory(target_dir)

    # write out workload file
    _write_workload(workload, os.path.dirname(os.path.dirname(target_dirs[0])), args) 

    previous_throughput = _read_existing_throughput(target_dirs[0],args)

    if (args.density) and ("fixed-streams" in workload._document["measurement"]["density"] or
                           "starting-streams" in workload._document["measurement"]["density"]
                           or previous_throughput) and (not args.throughput):
        throughput = previous_throughput
    elif ("throughput" in workload._document["measurement"]):
        runner_config = validate(runner_config_path, args.schemas)
        if ("throughput" in runner_config):
            if (not args.default_config):
                runner_config.update(runner_config["throughput"])
            runner_config.pop("throughput")
            
        apply_overrides(runner_config,args.runner_overrides)
        
        throughput = _measure_throughput(task,
                                         workload,
                                         args,
                                         target_dirs[0],
                                         runner_config)
        
    if ("density" in workload._document["measurement"]):
        runner_config = validate(runner_config_path, args.schemas)
        if ("density" in runner_config):
            if (not args.default_config):
                runner_config.update(runner_config["density"])
            runner_config.pop("density")
            
        apply_overrides(runner_config,args.runner_overrides)
  
        density = _measure_density(throughput,
                                   task,
                                   workload,
                                   args,
                                   target_dirs[1],
                                   runner_config)


def download(args):
    _download_pipeline(args.pipeline,
                      args)


def list_pipeline_runners(pipeline_path):
    for root, directories, files in os.walk(os.path.dirname(pipeline_path)):
        return [path.replace(".config.yml","") for path in files if path.endswith(".config.yml")]

def list_pipelines(args):

    descriptions = []
    for pipeline,pipeline_path in zip(args.pipelines[0],args.pipelines[1]):
        pipeline_config = PipelineConfig(pipeline_path,args)

        models= []
        runners = list_pipeline_runners(pipeline_path)
        for key, value in pipeline_config._document.items():
            if "model" in key:
                if isinstance(value, list):
                    models.extend(value)
                else:
                    models.append(value)
                    
        
        descriptions.append({"Pipeline":pipeline,
                             "Task":pipeline_config._namespace.task,
                             "Models":"\n".join(models),
                             "Runners":"\n".join(runners)})
    
    print(tabulate(descriptions,headers={'name':'name','models':'models','task':'task'},tablefmt="grid"))
    
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
        workload_name = workload_name.replace("workload.yml","").replace("workload.json","").strip('.')
        workload_name = os.path.basename(workload.media) if workload_name == "" else workload_name
        args.workload_name = workload_name
        args.workload_root = os.path.join(args.
                                          workspace_root,
                                          workload.pipeline,
                                          "workloads",
                                          os.path.basename(workload.media))

        
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
    
        subprocess.run(command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


    directories = [os.path.join(args.workload_root,suffix) for suffix in ["input", "reference"]]
                
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

def _iteration_stats(iteration):
    values = {}
    for stream_result in iteration:
        for key,value in stream_result.items():
            values.setdefault(key,[]).append(value[0])
    return values
        
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

    last = []
    second_to_last = []
    if (results):
        iteration = results[-1]
        last.append("Streams: {}".format(len(iteration)))
        last.extend(_density_result_strings(iteration))
        values = _iteration_stats(iteration)
        last.append("Min: {:04.4f} Max: {:04.4f} Avg: {:04.4f}".format(min(values["avg"]),
                                                                    max(values["avg"]),
                                                                    mean(values["avg"])))
                                                                                                                
        if (len(results)>1):
            iteration = results[-2]
            second_to_last.append("Streams: {}".format(len(iteration)))
            second_to_last.extend(_density_result_strings(iteration))
            values = _iteration_stats(iteration)
            second_to_last.append("Min: {:04.4f} Max: {:04.4f} Avg: {:04.4f}".format(min(values["avg"]),
                                                                                  max(values["avg"]),
                                                                                  mean(values["avg"])))


    table = {'Pipeline':workload.pipeline,
             'Runner':runner}
    
    if (second_to_last):
        table[second_to_last[0]]="\n".join(second_to_last[1:])

    if (last):
        table[last[0]]="\n".join(last[1:])

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

    table = {'Pipeline':workload.pipeline,
             'Runner':runner,
             'Media':workload._namespace.media,
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
        _max = config[range_name][1]

    if _min < 1:
        _min = config["fps"] - _min
    if _max < 1:
        _max = config["fps"] + _max
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

def _density_result_strings(range_results):
    stream_template = "Stream: {0:04d}"
    stream_results = []
    fps_template = "{0:04.4f} {1}"
    passed = {True:"Pass",
              False:"Fail"}
    for index,range_result in enumerate(range_results):
        
        stream_results.append("{} {}".format(
            stream_template.format(index),
        " ".join(["{}: {}".format(key.title(),fps_template.format(value[0],passed[value[1]]))
                  for key,value in range_result.items()])))
    return stream_results

def _print_density_result(range_results):
    print_action("Density Result",_density_result_strings(range_results))
                      
def _measure_density(throughput,
                     task,
                     workload,
                     args,
                     target_dir,
                     runner_config):
    config = workload._document["measurement"].get("density",{})
    
    if ("fixed-streams" in config):
        num_streams = config["fixed-streams"]
        config["max-streams"] = num_streams
        config["max-iterations"] = 1
    elif ("starting-streams" in config):
        num_streams = config["starting-streams"]
    else:
        # Use throughput to estimate stream density
        num_streams = min(config["max-streams"], math.floor(throughput / workload._document["measurement"]["density"]["fps"]))
        num_streams = max(config["min-streams"], num_streams)
        
        
    print_action("Measuring Stream Density",[config])

    results_directory = target_dir
    
    create_directory(results_directory)
    
    done = False
    density = 0
    first_result = None
    current_result = None
    iteration = 0
    iteration_results = []
    max_iterations = config["max-iterations"]
    frame_rate = config["fps"]
    if (not config["limit-frame-rate"]):
        frame_rate = -1
    
    while (
            (first_result == current_result)
            and (num_streams>=config["min-streams"]) and (num_streams<=config["max-streams"])
            and (max_iterations<0 or iteration < max_iterations)
    ):
        runners = []

        print_action("Stream Density",
                     ["Iteration: {}".format(iteration,),
                      "Number of Streams: {}".format(num_streams)])

        
        for stream_index in range(num_streams):

            run_directory = os.path.join(target_dir,
                                         "iteration_{}".format(iteration),
                                         "stream_{}".format(stream_index))
            create_directory(run_directory)

            source, sink, runner  = task.run(run_directory,
                                             runner_config,
                                             config["warm-up"],
                                             frame_rate,
                                             config["sample-size"])


            time.sleep(2)

            runners.append((source,sink,runner))

        results = _wait_for_task(runners, config["duration"]+(4*num_streams))
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
                          target_dir,
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
            selected = result["throughput"]["config"]["select"]
            return result["throughput"]["FPS"].get(selected,None)
    return None
    
def _measure_throughput(task,
                        workload,
                        args,
                        target_dir,
                        runner_config):
  
    run_directory = target_dir
    
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
                                 args.workload_name + ".workload.yml")
    
    with open(workload_path,"w") as workload_file:
        yaml.dump(workload._document,
                  workload_file,
                  sort_keys=False)
        
    
