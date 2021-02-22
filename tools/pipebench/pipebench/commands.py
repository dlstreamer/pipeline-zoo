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
import time
from statistics import mean
import subprocess

def _get_runner_config_path(measurement, workload, args):

    candidates = []
    template = os.path.join(args.workspace_root,
                            workload.pipeline,
                            "{runner}{platform}{config}.config.{extension}")
    
    configs = []
    if (args.runner_config):
        configs.append(args.runner_config)
    else:
        configs.append(measurement)
        configs.append(None)

    platforms = []
    if (args.platform):
        platforms.append(args.platform)
    else:
        platforms.append(None)

    for config in configs:
        for platform in platforms:
            candidates.append(template.format(runner = args.runner,
                                              config = ".{}".format(config) if config else "",
                                              platform = ".{}".format(platform) if platform else "",
                                              extension = "yml"))
            candidates.append(template.format(runner = args.runner,
                                              config = ".{}".format(config) if config else "",
                                              platform = ".{}".format(platform) if platform else "",
                                              extension = "json"))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
        
    args.parser.error("Runner config not found in workspace, candidates: {}".format(candidates,))

def _get_numa_nodes(args):
    numa_nodes = None
    try:
        result = subprocess.run(["numactl","--hardware"], stdout=subprocess.PIPE, universal_newlines=True)
        available_split = result.stdout.split('\n')[0].split()
        if available_split[0]=="available:":
            numa_nodes = int(available_split[1])
    except Exception as error:
        print(error)

    if (not numa_nodes):
        args.parser.error("Can't get number of numa nodes!")
    return numa_nodes

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

    target_dir_suffix = "{runner}{platform}{config}".format(runner = args.runner,
                                                            platform = ".{}".format(args.platform) if args.platform else "",
                                                            config = ".{}".format(args.runner_config) if args.runner_config else "")
    
    # create output folder for runner

    measurements = ["throughput"]

    if ("density" in workload._document["measurement"]):
        measurements.append("density.{}fps".format(workload._namespace.measurement.density.fps))

    timestamp = ""
    
    if (args.add_timestamp):
        timestamp = "_{}".format(int(time.time()))
        
    target_dirs = [ os.path.join(args.pipeline_root,
                                 "measurements",
                                 args.workload_name+timestamp,
                                 workload.scenario.source,
                                 measurement,
                                 target_dir_suffix)
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
    if (args.save_workload):
        _write_workload(workload, args.pipeline_root, args)

    previous_throughput = _read_existing_throughput(target_dirs[0],args)

    if (args.density) and ("fixed-streams" in workload._document["measurement"]["density"] or
                           "starting-streams" in workload._document["measurement"]["density"]
                           or previous_throughput) and (not args.throughput):
        throughput = previous_throughput
    elif ("throughput" in workload._document["measurement"]):
        runner_config_path = _get_runner_config_path("throughput",
                                                     workload,
                                                     args)
        runner_config = validate(runner_config_path, args.schemas, args.runner_overrides)

        if (args.save_runner_config and runner_config):
            _write_runner_config(runner_config, args)
                    
        throughput = _measure_throughput(task,
                                         workload,
                                         args,
                                         target_dirs[0],
                                         runner_config)
        if (not throughput):
            print("No throughput calculated. Check pipeline runner logs for errors.")
        
    if ("density" in workload._document["measurement"]):
        runner_config_path = _get_runner_config_path("density",
                                                     workload,
                                                     args)
        runner_config = validate(runner_config_path, args.schemas, args.runner_overrides)

        if (args.save_runner_config and runner_config):
            _write_runner_config(runner_config, args)

            
        density = _measure_density(throughput,
                                   task,
                                   workload,
                                   args,
                                   target_dirs[1],
                                   runner_config)
        if (not density):
            print("No density calculated. Check pipeline runner logs for errors.")
      


def download(args):
    _download_pipeline(args.pipeline,
                      args)


def list_pipeline_runners(pipeline_path):

    for root, directories, files in os.walk(os.path.dirname(pipeline_path)):
        return [path.replace(".config.yml","") for path in files if path.endswith(".config.yml") and (len(path.split('.'))==3)]

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
        if (args.save_workload):
            workload_name = args.save_workload
        args.workload_name = workload_name
        args.workload_root = os.path.join(args.
                                          workspace_root,
                                          workload.pipeline,
                                          "workloads",
                                          os.path.basename(workload.media),
                                          workload.scenario.source)

        
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

    template = "{stream} FPS:{stats.fps:04.4f} Min: {stats.min:04.4f} Max: {stats.max:04.4f} Avg: {stats.avg:04.4f} {end}"
    output = []
    for index, (source, sink, runner_process, _) in enumerate(runners):
        if (not source or source.is_alive()):
            
            stats = sink.get_fps()
            if stats.start and stats.end:
                end = "Start: {:.4f} End: {:.4f}".format(stats.start,stats.end)
            else:
                end = ""

            if (stats.min<sys.maxsize):
                total_fps += stats.fps
                output.append(template.format(stream=stream_template.format(index=index),
                                              stats=stats,
                                              end=end))
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
                          totals["avg"],
                          None,
                          None)
        
        output.append(template.format(stream="Total:      ",
                                      stats=stats,
                                      end=""))
                          
    if (output):
        print_action("Frames Per Second", output)

known_return_codes = [-9, 0]
def _check_return_codes(return_codes):
    unknown_return = ["Return Code: {} Output Directory: {}".format(return_code[0],return_code[1])
                      for return_code in return_codes if return_code[0] not in known_return_codes]
    if (unknown_return):
        print("Error - Check Output Directory:\n\n\t{}".format(
            "\n\t".join(unknown_return)))
        sys.exit(1)


def _wait_for_task(runners, duration):
    results = []
    return_codes = []
    start = time.time()
    totals = {}
    for (source, sink, runner_process, run_directory) in runners:
        while(((not source or source.is_alive()) and (runner_process.poll() is None))
              and ((time.time()-start) < duration)):
            if (source):
                source.join(1)
            else:
                time.sleep(1)
            _print_fps(runners, totals)
        if (source):
            source.stop()
        if (source and source.connected):
            source.join()
        
        runner_process.kill()
        runner_process.wait()
        sink.stop()
        if (sink.connected):
            sink.join(10)
        results.append(sink.get_fps())
        return_codes.append((runner_process.returncode,run_directory))
        
    if ("total" in totals):
        del totals["total"]
    _check_return_codes(return_codes)
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
    if ( not config["per-stream"]):
        stream_template ="Total"
    for iteration_index,result in enumerate(results):
        iteration_result = {}
        for stream_index,stream_result in enumerate(result[0]):
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
        last.append("Streams: {}".format(iteration[1]))
        last.extend(_density_result_strings(iteration[0],config))
        if (len(iteration[0])>1):
            values = _iteration_stats(iteration[0])
            last.append("Min: {:04.4f} Max: {:04.4f} Avg: {:04.4f}".format(min(values["avg"]),
                                                                           max(values["avg"]),
                                                                           mean(values["avg"])))
                                                                                                                
        if (len(results)>1):
            iteration = results[-2]
            second_to_last.append("Streams: {}".format(iteration[1]))
            second_to_last.extend(_density_result_strings(iteration[0],config))
            if (len(iteration[0])>1):
                values = _iteration_stats(iteration[0])
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

    if (config["select"] not in results):
        return
        
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
    ranges = {'min':_normalize_range(config,"minimum-range"),
              'avg':_normalize_range(config,"average-range")}
    
    if (config["per-stream"]):
        per_stream_results = results[0]
        range_results = [_check_ranges(stream_result,ranges) for stream_result in per_stream_results]
    else:
        number_of_streams = len(results[0])
    
        total_result = FpsReport(0,
                                 results[1]["min"]/number_of_streams,
                                 results[1]["max"]/number_of_streams,
                                 0,
                                 results[1]["avg"]/number_of_streams,
                                 None,
                                 None)
        
        range_results = [_check_ranges(total_result, ranges)]

    for result in range_results:
        for key in result:
            if not result[key][1]:
                return False, range_results
    return True, range_results

def _density_result_strings(range_results, config):
    stream_template = "Stream: {0:04d}"
    stream_results = []
    fps_template = "{0:04.4f} {1}"
    passed = {True:"Pass",
              False:"Fail"}
    for index,range_result in enumerate(range_results):
        if (not config["per-stream"]):
            stream_template ="Total"
        stream_results.append("{} {}".format(
            stream_template.format(index),
        " ".join(["{}: {}".format(key.title(),fps_template.format(value[0],passed[value[1]]))
                  for key,value in range_result.items()])))
    return stream_results

def _print_density_result(range_results, config):
    print_action("Density Result",_density_result_strings(range_results,config))
                      
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
    elif throughput:
        # Use throughput to estimate stream density
        num_streams = min(config["max-streams"], math.floor(throughput / workload._document["measurement"]["density"]["fps"]))
        num_streams = max(config["min-streams"], num_streams)
    else:
        print("No starting density specified and no throughput result")
        sys.exit(1)

    numa_nodes = None
    numa_node = None
    if (config["numa-aware"]):
        numa_nodes = _get_numa_nodes(args)

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

            if (numa_nodes):
                numa_node = stream_index % numa_nodes

            source, sink, runner  = task.run(run_directory,
                                             runner_config,
                                             config["warm-up"],
                                             frame_rate,
                                             config["sample-size"],
                                             numa_node)

            runners.append((source,sink,runner,run_directory))

        results = _wait_for_task(runners, config["duration"] + 10)
        success, density_result =_check_density(results, config)
        _print_density_result(density_result, config)
        print_action("Stream Density",
                     ["Iteration: {}".format(iteration,),
                      "Number of Streams: {}".format(num_streams),
                      "Passed: {}".format(success)])
        iteration_results.append((density_result,num_streams))
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
    return density

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

    per_stream_results, totals = _wait_for_task([(source, sink, runner,run_directory)],
                                                config["duration"])

    _write_throughput_result(run_directory, workload, config, totals, args.runner)
    return totals.get(config['select'],None)
    

def _write_runner_config(config, args):
    config_path = os.path.join(args.pipeline_root,
                               args.runner+"{}.{}.{}".format(
                                   ".{}".format(args.platform) if args.platform else "",
                                   args.save_runner_config,
                                   "config.yml"))
    with open(config_path,"w") as config_file:
        yaml.dump(config,
                  config_file,
                  sort_keys=False)
        
def _write_workload(workload, target_dir, args):

    workload_path = os.path.join(target_dir,
                                 args.workload_name + ".workload.yml")
    
    with open(workload_path,"w") as workload_file:
        yaml.dump(workload._document,
                  workload_file,
                  sort_keys=False)
        
    
