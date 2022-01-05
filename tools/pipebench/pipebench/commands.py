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
from threading import Semaphore


def _get_runner_settings(measurement, args, add_default_platform=False, no_overrides=False):
    runner_settings_path = _get_runner_settings_path(measurement, args, add_default_platform)
    if no_overrides:
        return validate(runner_settings_path, args.schemas), runner_settings_path
    else:
        return validate(runner_settings_path, args.schemas, args.runner_overrides), runner_settings_path

def _get_runner_settings_path(measurement, args, add_default_platform):

    candidates = []
    template = os.path.join(args.pipeline_root,
                            "{runner}{setting}{platform}.runner-settings.{extension}")
    
    settings = []
    if (args.runner_settings):
        settings.append(args.runner_settings)
    else:
        settings.append(measurement)
        settings.append(None)
    platforms = []
    if (args.platform):
        platforms.append(args.platform)
        if add_default_platform:
            platforms.append(None)
    else:
        platforms.append(None)

    for setting in settings:
        for platform in platforms:
            candidates.append(template.format(runner = args.runner,
                                              setting = ".{}".format(setting) if setting else "",
                                              platform = ".{}".format(platform) if platform else "",
                                              extension = "yml"))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
        
    args.parser.error("Runner settings not found in workspace, candidates: {}".format(candidates,))

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


def _default_media(args):
    media_list_path = os.path.join(args.pipeline_root,"media.list.yml")
    document = validate(media_list_path,args.schemas)
    if (document) and isinstance(document,list):
        return document[0]
    return None

def _create_default_measurement_settings(args, overrides):
    with tempfile.TemporaryDirectory() as temp_directory:
        measurement_settings_path = "{}/{}.measurement-settings.yml".format(
            temp_directory,
            args.measurement)
        measurement_settings = {}
        measurement_settings["media"]=_default_media(args)
    
        with open(measurement_settings_path,"w") as measurement_settings_file:
            if args.measurement=="density":
                measurement_settings["streams"] = 0
                measurement_settings["target-condition"] = "stream"
            json.dump(measurement_settings,
                      measurement_settings_file)
        return validate(measurement_settings_path,args.schemas,overrides),measurement_settings_path

def _get_measurement_overrides(args):
    overrides=[]
    for key in args.schemas["measurement-settings"]["properties"]:
        if key in args:
            overrides.append((key,getattr(args,key)))
        if key.replace("-","_") in args:
            overrides.append((key,getattr(args,key.replace("-","_"))))
    return overrides

def _load_measurement_settings(args):

    candidates = []
    platforms = []
    if args.platform:
        platforms.append(args.platform)
    platforms.append(None)

    overrides = _get_measurement_overrides(args)
    
    template = os.path.join(args.workspace_root,
                            args.pipeline,
                            "{measurement_name}{platform}"
                            ".measurement-settings.yml")

    if args.measurement_settings:
        if os.path.isfile(os.path.abspath(args.measurement_settings)):
            if not args.measurement_settings.endswith(".measurement-settings.yml"):
                args.parser.error("Measurement settings must end in measurement-settings.yml")
            candidates.append(os.path.abspath(args.measurement_settings))
        else:
            for platform in platforms:
                candidates.append(template.format(measurement_name=
                                                  args.measurement_settings,
                                                  platform=".{}".format(platform)
                                                  if platform else ""))
    elif args.measurement:
        for platform in platforms:
            candidates.append(template.format(measurement_name=
                                              args.measurement,
                                              platform=".{}".format(platform)
                                              if platform else ""))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return validate(candidate,args.schemas,overrides), candidate

    if not args.measurement_settings and args.measurement in ["density","throughput"]:
        return _create_default_measurement_settings(args, overrides)
        
    args.parser.error("Measurement settings not found in workspace.\n\tCandidates: {}".format(candidates))

def _get_run_number(target_directory):
    previous_runs = []
    if not os.path.isdir(target_directory):
        return 0
    for path in os.listdir(target_directory):
        if os.path.isdir(os.path.join(target_directory,path)):
            if path.startswith("run-"):
                try:
                    path = path.replace("run-","")
                    previous_runs.append(int(path))
                except:
                    pass

    max_previous = max(previous_runs)
    return max_previous+1

def _prepare_run_directory(args):
    pipeline_path = find_pipeline(args.pipeline, args)
        
    if (not pipeline_path):
        args.parser.error("Pipeline {} not found in workspace".format(
            args.pipeline,))
       
    args.pipeline_root = os.path.dirname(pipeline_path)

    measurement_settings, measurement_settings_path = _load_measurement_settings(args)


    task = Task.create_task(measurement_settings, pipeline_path, args)

    media_name = os.path.basename(measurement_settings["media"])
    
    args.workload_root = os.path.join(args.pipeline_root,
                                      ".workloads",
                                      media_name,
                                      measurement_settings["scenario"]["source"])
    
    _prepare(task, measurement_settings, args)

        
    runner_settings, runner_settings_path = _get_runner_settings(
        args.measurement,
        args)

    if not "streams-per-process" in runner_settings:
        runner_settings["streams-per-process"] = measurement_settings["streams-per-process"]
    
    if "streams_per_process" in vars(args):
        runner_settings["streams-per-process"] = args.streams_per_process
    
    if measurement_settings["streams-per-process"] != 1:
        runner_settings["streams-per-process"] = measurement_settings["streams-per-process"]

    runner_settings_name = (os.path.basename(runner_settings_path).
                            replace(".runner-settings.yml","").
                            replace(".{}".format(args.measurement),
                                    ""))
    
    target_root = args.pipeline_root

    if (args.measurement_directory):
        target_root = os.path.abspath(
            os.path.join(args.measurement_directory,
                         os.path.basename(args.pipeline_root)))


    target_dir = os.path.join(target_root,
                              "measurements",
                              args.measurement,
                              runner_settings_name)

    if (args.force):
        try:
            shutil.rmtree(target_dir)
        except Exception as error:
            pass

    run_directory = os.path.join(target_dir,
                                 "run-{:04d}".format(_get_run_number(target_dir)))

    create_directory(run_directory)

    _write_measurement_settings(measurement_settings,
                                args.measurement,
                                run_directory,
                                args)

    if args.save_measurement_settings:
        measurement_settings_name = "{}{}".format(args.save_measurement_settings,
                                                  ".{}".format(args.platform) if args.platform else "")

        _write_measurement_settings(measurement_settings,
                                    measurement_settings_name,
                                    args.pipeline_root,
                                    args)
    _write_runner_settings(runner_settings,
                           runner_settings_name,
                           run_directory,
                           args)
    if args.save_runner_settings:
        runner_settings_name = "{}.{}{}".format(args.runner,
                                                args.save_runner_settings,
                                                ".{}".format(args.platform) if args.platform else "")
        _write_runner_settings(runner_settings,
                               runner_settings_name,
                               args.pipeline_root,
                               args)

    shutil.copy(os.path.join(args.workload_root, "systeminfo.json"),
                run_directory)
    args.measurement_settings_path = measurement_settings_path
    args.runner_settings_path = runner_settings_path
    return run_directory, measurement_settings, runner_settings, task

def _estimate_starting_streams(args, run_directory, task, measurement_settings):
    runner_settings, _ = _get_runner_settings("throughput",
                                              args,
                                              True,
                                              no_overrides=True)
    temp_run_directory = os.path.join(os.path.dirname(run_directory),
                                      ".throughput")
    create_directory(temp_run_directory)
    sources,sinks,runner = task.run(temp_run_directory,
                                    runner_settings,
                                    measurement_settings["warm-up"],
                                    -1,
                                    measurement_settings["sample-size"])
    per_stream_results, totals, number_of_runners = _wait_for_task([(sources,sinks,runner,temp_run_directory)],
                                                measurement_settings["duration"]," PRE")
    return math.floor(totals["avg"]/measurement_settings["target-fps"])

def _run_iteration(num_streams,
                   streams_per_process,
                   numa_nodes,
                   runner_settings,
                   measurement_settings,
                   target_dir,
                   task,
                   iteration,
                   max_processes):
    semaphore = Semaphore(0)
    process_index = 0
    runners = []
    if not streams_per_process:
        streams_per_process = num_streams
        if max_processes:
            streams_per_process = math.ceil(num_streams / max_processes)
    for stream_index in range(0, num_streams, streams_per_process):
        end_stream_index = stream_index + streams_per_process -1
        if end_stream_index >= num_streams:
            end_stream_index = num_streams - 1
        if streams_per_process > 1:
            run_directory_suffix = "process-{:04d}-streams-{:04d}-{:04d}".format(
                process_index,
                stream_index,
                end_stream_index)
        else:
            run_directory_suffix = "process-{:04d}-stream-{:04d}".format(
                process_index,
                stream_index)

        run_directory = os.path.join(target_dir,
                                     "iteration-{:04d}".format(iteration),
                                     run_directory_suffix)
        create_directory(run_directory)

        if (numa_nodes):
            numa_node = stream_index % numa_nodes

        sources, sinks, runner  = task.run(run_directory,
                                           runner_settings,
                                           measurement_settings["warm-up"],
                                           measurement_settings["target-fps"],
                                           measurement_settings["sample-size"],
                                           semaphore = semaphore,
                                           numa_node = numa_node,
                                           starting_stream_index = stream_index,
                                           number_of_streams=(end_stream_index-stream_index+1))

        runners.append((sources,sinks,runner,run_directory))
        process_index += 1

    for stream_index in range(num_streams): 
        semaphore.release()

    return _wait_for_task(runners, measurement_settings["duration"] + 10,"{:04d}".format(iteration))

def _summarize_measurement(args,
                           run_directory,
                           measurement_settings,
                           runner_settings):
    print("")
    print(" Pipeline:\n\t{}\n".format(args.pipeline))
    print(" Runner:\n\t{}".format(args.runner))
    print(" \t{}\n".format(os.path.basename(args.runner_settings_path)))
    print(" Media:\n\t{}\n".format(measurement_settings["media"]))
    print(" Measurement:\n\t{}".format(args.measurement))
    print(" \t{}\n".format(os.path.basename(args.measurement_settings_path)))
    print(" Output Directory:\n\t{}\n".format(run_directory))
    
def run(args):
    run_directory, measurement_settings, runner_settings, task = _prepare_run_directory(args)

    _summarize_measurement(args,
                           run_directory,
                           measurement_settings,
                           runner_settings)

    if (measurement_settings["streams"] == 0 and measurement_settings["starting-streams"] == 0
        and measurement_settings["target-condition"]!="total"):
        starting_streams = _estimate_starting_streams(args, run_directory, task, measurement_settings)
    else:
        starting_streams = (measurement_settings["streams"] if measurement_settings["streams"]
                            else measurement_settings["starting-streams"])
    numa_nodes = []
    if measurement_settings["numactl"]:
        numa_nodes = _get_numa_nodes(args)

    done = False
    min_streams = measurement_settings["min-streams"]
    max_streams = measurement_settings["max-streams"] if measurement_settings["max-streams"] else sys.maxsize
    max_iterations = measurement_settings["max-iterations"] if measurement_settings["max-streams"] else sys.maxsize
    if measurement_settings["streams"]:
        max_iterations = 1
        
    starting_streams = max(min_streams,
                           starting_streams)
    
    starting_streams = min(max_streams,
                           starting_streams)
    if not starting_streams:
        starting_streams = 1
        
    min_failure = -1
    max_success = -1
    max_success_iteration = -1
    min_failure_iteration = -1
    streams_per_process = runner_settings["streams-per-process"]
    iteration = 0
    first_result = None
    max_processes = measurement_settings["max-processes"]
    if max_processes:
        max_streams = min(max_streams,
                          streams_per_process * max_processes)
        if not max_streams:
            max_streams = sys.maxsize
            
    num_streams = starting_streams
    iteration_results = []
    iteration_results_map = {}

    done = False
    density = 0
    first_result = None
    current_result = None

    search_method = measurement_settings["search-method"]
    current_total_fps = 0
    
    while ( ((max_success==-1) or
             (min_failure==-1) or
             (min_failure-max_success>1)) and
            (num_streams>=min_streams) and
            (num_streams<=max_streams) and
            (max_iterations==0 or iteration <max_iterations)):


        results = _run_iteration(num_streams,
                                 streams_per_process,
                                 numa_nodes,
                                 runner_settings,
                                 measurement_settings,
                                 run_directory,
                                 task,
                                 iteration,
                                 max_processes)
        total_fps = sum ([stream_result.avg for stream_result in results[0]])
        
            
        success, density_result = _check_density(results, measurement_settings)
        if args.verbose_level>0:
            _print_density_result(density_result,measurement_settings)

        iteration_results.append((density_result,num_streams,results[2]))
        iteration_results_map[num_streams] = success
        
        if (first_result is None):
            first_result = success
        current_result = success
        old_num_streams = num_streams
        calculated_num_streams = int(sum ([stream_result.avg for stream_result in results[0]])/measurement_settings['target-fps'])

        if measurement_settings["target-condition"] == "total":
            if total_fps >current_total_fps:
                current_total_fps = total_fps
                max_success_iteration = iteration
                density=num_streams
                iteration += 1
                num_streams+=1
                continue
            else:
                min_failure_iteration = iteration
                break
        
        
        if (success):
            calculated_num_streams += 1
            if (density < num_streams):
                density = num_streams
            if (num_streams > max_success):
                max_success = num_streams
                max_success_iteration = iteration

            if search_method == "linear":
                num_streams += 1
            else:
                if (min_failure==-1):
                    num_streams *= 2
                else:
                    num_streams = int(((min_failure - max_success) / 2) + max_success)
                if ((calculated_num_streams < num_streams) and
                    (calculated_num_streams > max_success) and
                    (calculated_num_streams not in iteration_results_map)
                ):
                    num_streams = calculated_num_streams
        else:
            if (min_failure==-1) or (num_streams < min_failure):
                min_failure = num_streams
                min_failure_iteration = iteration

            if search_method == "linear":
                num_streams -= 1
            else:
                if (max_success == -1):
                    num_streams = int(num_streams / 2)
                else:
                    num_streams = int(((min_failure - max_success) / 2) + max_success)
                if ((calculated_num_streams > num_streams) and
                    (calculated_num_streams < min_failure) and
                    (calculated_num_streams not in iteration_results_map)):
                    num_streams = calculated_num_streams
  #              elif (calculated_num_streams-1 > num_streams) and (calculated_num_streams-1 not in iteration_results_map):
   #                 num_streams = calculated_num_streams-1
        
        if (num_streams>max_streams):
            num_streams = max_streams

        if (num_streams<min_streams):
            num_streams = min_streams
        
        if (num_streams == old_num_streams) or (num_streams in iteration_results_map):
            break

        iteration += 1
        
    _write_density_result(density,
                          run_directory,
                          args.pipeline,
                          measurement_settings,
                          iteration_results,
                          min_failure_iteration,
                          max_success_iteration,
                          args.runner,
                          runner_settings,
                          args)      


def download(args):
    _download_pipeline(args.pipeline,
                      args)


def list_pipeline_runners(pipeline_path):

    for root, directories, files in os.walk(os.path.dirname(pipeline_path)):
        return set([path.replace(".runner-settings.yml","").split('.')[0] for path in files if path.endswith(".runner-settings.yml")])

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

    verbose_option = "-v " * args.verbose_level
    
    cmd = shlex.split("python3 {0} -d {1} {2} {3}".format(downloader, args.workspace_root, pipeline, verbose_option))
    
    return cmd

def _download_pipeline(pipeline, args):

    target_dir = os.path.join(args.workspace_root,pipeline)
    
    if (args.force):
        try:
            shutil.rmtree(target_dir)
        except Exception as error:
            pass

    if (not os.path.isdir(target_dir)):
        print_action("Downloading {}".format(pipeline))
                       
        command = _create_download_command(pipeline,args)

        output = subprocess.DEVNULL if args.silent else None
        
        subprocess.run(command, stdout=output, stderr=output)
        
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
        if getattr(workload._namespace,"use-reference-detections",False):
            workload_name+=".using-reference-detections"
            
        args.workload_name = workload_name

        media_name = os.path.basename(workload.media)

        if getattr(workload._namespace,"use-reference-detections",False):
            media_name+=".using-reference-detections"
        
        args.workload_root = os.path.join(args.
                                          workspace_root,
                                          workload.pipeline,
                                          "workloads",
                                          media_name,
                                          workload.scenario.source)

        
        return workload
    except Exception as error:
        args.parser.error("Invalid workload: {}, error: {}".format(args.workload,error))

    return None


def _prepare(task, measurement_settings, args):
            
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

    timeout = None
    task.prepare(args.workload_root, timeout)
    
    
def _print_fps(runners, totals, iteration):

    results = []
    output = []
    stream_index = 0
    for (sources, sinks, runner_process, _) in runners:
        for index, source in enumerate(sources):
            if (not source or source.is_alive()):
                stats = sinks[index].get_fps()
                results.append(stats)

            stream_index+=1

    stream_count = len([stream_result.avg for stream_result in results if stream_result.avg !=0 ])
    average = mean ([stream_result.avg for stream_result in results])
    minimum = min  ([stream_result.avg for stream_result in results])
    maximum = max  ([stream_result.avg for stream_result in results])
    total = sum ([stream_result.avg for stream_result in results])

    print("="*72)
    output = "Iteration   Streams  Processes    Minimum   Average   Maximum      Total"
    print(output)
    print("="*72)
    output = "     {}      {:04d}       {:04d}  {:9.4f} {:9.4f} {:9.4f}  {:9.4f}".format(iteration,
                                                                                             stream_count,
                                                                                             len(runners),
                                                                                             minimum,
                                                                                             average,
                                                                                             maximum,
                                                                                             total)
    print(output)
    print("="*72,"\n")
    
    if (len(runners) == 1):
        totals["total"] = stats.fps
        totals["min"] = stats.min
        totals["max"] = stats.max
        totals["avg"] = stats.avg
                          
    return results

known_return_codes = [-9, -15, 0]
def _check_return_codes(return_codes):
    unknown_return = ["Return Code: {} Output Directory: {}".format(return_code[0],return_code[1])
                      for return_code in return_codes if return_code[0] not in known_return_codes]
    if (unknown_return):
        print("Error - Check Output Directory:\n\n\t{}".format(
            "\n\t".join(unknown_return)))
        sys.exit(1)


def _wait_for_task(runners, duration, iteration=None):
    results = []
    return_codes = []
    start = time.time()
    totals = {}
    for (sources, sinks, runner_process, run_directory) in runners:
        for source in sources:
            while(((not source or source.is_alive()) and (runner_process.poll() is None))
                  and ((time.time()-start) < duration)):
                if (source):
                    source.join(1)
                else:
                    time.sleep(1)
                results = _print_fps(runners, totals, iteration)

            if (source):
                source.stop()
            if (source and source.connected):
                source.join()

        runner_process.terminate()
        try:
            runner_process.wait(10)
        except:
            runner_process.kill()
        runner_process.wait()
        for sink in sinks:
            sink.stop()
            if (sink.connected):
                sink.join(10)
        return_codes.append((runner_process.returncode,run_directory))
        
    if ("total" in totals):
        del totals["total"]
    _check_return_codes(return_codes)
    return results, totals, len(runners)

def _iteration_stats(iteration):
    values = {}
    for stream_result in iteration:
        for key,value in stream_result.items():
            values.setdefault(key,[]).append(value[0])
    return values

def _write_result_json(density,
                       run_directory,
                       pipeline,
                       measurement_settings,
                       results,
                       min_failure_iteration,
                       max_success_iteration,
                       runner,
                       runner_settings,
                       args):

    iteration = results[max_success_iteration]
    values = _iteration_stats(iteration[0])
    minimum = min(values["avg"])
    maximum = max(values["avg"])
    average = mean(values["avg"])
    total = sum(values["avg"])
    streams = density
    processes = results[max_success_iteration][2]

    iteration_results = {}
    stream_template = "Stream: {0:04d}"
    iteration_template="Iteration: {0:04d}"
    for iteration_index,result in enumerate(results):
        iteration_result = {}
        for stream_index,stream_result in enumerate(result[0]):
            iteration_result[stream_template.format(stream_index)] = stream_result

        iteration_values = _iteration_stats(result[0])
        iteration_minimum = min(iteration_values["avg"])
        iteration_maximum = max(iteration_values["avg"])
        iteration_average = mean(iteration_values["avg"])
        iteration_total = sum(iteration_values["avg"])
        iteration_streams = len(result[0])
        iteration_processes = result[2]
        iteration_result["streams"]=iteration_streams
        iteration_result["max"]=iteration_maximum
        iteration_result["min"]=iteration_minimum
        iteration_result["avg"]=iteration_average
        iteration_result["total"]=iteration_total
        iteration_result["processes"]=iteration_processes
        iteration_results[iteration_template.format(iteration_index)]=iteration_result
    
    result = {args.measurement: {
        "streams":density,
        "max":maximum,
        "min":minimum,
        "avg":average,
        "total":total,
        "processes":processes,
        "iterations":iteration_results,
        "measurement_settings":measurement_settings,
        "runner_settings":runner_settings,
        "command_line":subprocess.list2cmdline(sys.argv)
    }}
    
    result_file_name = os.path.join(run_directory,
                                    "result.json")

    with open(result_file_name,"w") as result_file:
        json.dump(result, result_file, indent=4)

    

def _write_density_result(density,
                          run_directory,
                          pipeline,
                          measurement_settings,
                          results,
                          min_failure_iteration,
                          max_success_iteration,
                          runner,
                          runner_settings,
                          args):
    
    _write_result_json(density,
                       run_directory,
                       pipeline,
                       measurement_settings,
                       results,
                       min_failure_iteration,
                       max_success_iteration,
                       runner,
                       runner_settings,
                       args)
    

    last = []
    second_to_last = []
    if (results):
        iteration = results[max_success_iteration]
        last.append("Streams: {}".format(iteration[1]))
        if args.verbose_level>0:
            last.extend(_density_result_strings(iteration[0],measurement_settings))
        values = _iteration_stats(iteration[0])
        last.append("Min: {:04.4f} Max: {:04.4f} Avg: {:04.4f} Total: {:04.4f}".format(min(values["avg"]),
                                                                                           max(values["avg"]),
                                                                                           mean(values["avg"]),
                                                                                           sum(values["avg"])))
                                                                                                                
        if (len(results)>1):
            iteration = results[min_failure_iteration]
            second_to_last.append("Streams: {}".format(iteration[1]))
            if args.verbose_level>0:
                second_to_last.extend(_density_result_strings(iteration[0],measurement_settings))
            values = _iteration_stats(iteration[0])
            second_to_last.append("Min: {:04.4f} Max: {:04.4f} Avg: {:04.4f} Total: {:04.4f}".format(min(values["avg"]),
                                                                                                         max(values["avg"]),
                                                                                                         mean(values["avg"]),
                                                                                                         sum(values["avg"])))


    table = {'Pipeline':pipeline,
             'Runner':runner}
    
    if (second_to_last):
        table[second_to_last[0]]="\n".join(second_to_last[1:])

    if (last):
        table[last[0]]="\n".join(last[1:])

    headers = {key:key for key in table}
    print(tabulate([table],headers=headers))

    
def _normalize_range(config,range_name):
    if (not range_name in config):
        return None
    _min = config[range_name][0]
    _max = sys.maxsize
    if (len(config[range_name])>1):
        _max = config[range_name][1]

    if _min < 1:
        _min = config["target-fps"] - _min
    if _max < 1:
        _max = config["target-fps"] + _max
    return (_min,_max)

def _check_ranges(result, ranges):
    return {key:((getattr(result,key),(getattr(result,key)>=ranges[key][0] and getattr(result,key)<=ranges[key][1]))) for key in ranges if ranges[key]!=None}
    
def _check_density(results, config):
    success = True
    ranges = {'min':_normalize_range(config,"minimum-range"),
              'avg':_normalize_range(config,"target-range")}
    
    # if (config["target-condition"]=="stream"):
    #     per_stream_results = results[0]
    #     range_results = [_check_ranges(stream_result,ranges) for stream_result in per_stream_results]
    # else:
    #number_of_streams = len(results[0])
    per_stream_results = results[0]

    average = mean ([stream_result.avg for stream_result in per_stream_results])
    minimum = min  ([stream_result.avg for stream_result in per_stream_results])
    maximum = max  ([stream_result.avg for stream_result in per_stream_results])
    total_result = FpsReport(0,
                             minimum,
                             maximum,
                             0,
                             average,
                             None,
                             None)

    range_results = [_check_ranges(stream_result,ranges) for stream_result in per_stream_results]

#    range_results.append(_check_ranges(total_result, ranges))

    if config["target-condition"]=="stream":
        check_results = range_results
    else:
        check_results = [_check_ranges(total_result, ranges)]
    
    for result in check_results:
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
        #if (not config["target-condition"]=="stream"):
         #   stream_template ="Total"
        stream_results.append("{} {}".format(
            stream_template.format(index),
        " ".join(["{}: {}".format(key.title(),fps_template.format(value[0],passed[value[1]]))
                  for key,value in range_result.items()])))
    return stream_results

def _print_density_result(range_results, config):
    print_action("Iteration Result",_density_result_strings(range_results,config))
                      
def _read_existing_throughput(target_dir, args):
    path = os.path.join(target_dir,"result.json")
    if (os.path.isfile(path)):
        result = validate(os.path.join(target_dir,"result.json"),
                          args.schemas)
        if (result):
            selected = result["throughput"]["config"]["select"]
            return result["throughput"]["FPS"].get(selected,None)
    return None

    
def _write_runner_settings(runner_settings,
                           runner_settings_name,
                           target_dir,
                           args):
    template = os.path.join(target_dir,
                            "{settings}.runner-settings.{extension}")    
    
    settings_path = template.format(
                                    settings = "{}".format(runner_settings_name),
                                    extension = "yml")

    with open(settings_path,"w") as settings_file:
        yaml.dump(runner_settings,
                  settings_file,
                  sort_keys=False)


def _write_measurement_settings(measurement_settings,
                                measurement_name,
                                target_dir,
                                args):
    measurement_settings_path = os.path.join(target_dir,
                                             measurement_name+".measurement-settings.yml")

    with open(measurement_settings_path,"w") as measurement_settings_file:
        yaml.dump(measurement_settings,
                  measurement_settings_file,
                  sort_keys=False)

        
    
