'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import abc
import yaml
import json
import jsonschema
from jsonschema import Draft7Validator, validators, RefResolver
from types import SimpleNamespace
from pipebench.schema.documents import PipelineConfig
import os
from pipebench.schema.documents import rsetattr

def _set_namespace_value(namespace,path,value):
    current = namespace
    for segment in path[:-1]:
        if segment not in vars(current):
            setattr(current,segment,SimpleNamespace())

        current = getattr(current,segment)

    setattr(current,path[-1],value)


def _split_path(path):

    segments = []
    
    while 1:
        prefix, suffix = os.path.split(path)
        if prefix == path:  # sentinel for absolute paths
            segments.insert(0, prefix)
            break
        elif suffix == path: # sentinel for relative paths
            segments.insert(0, suffix)
            break
        else:
            path = prefix
            segments.insert(0, suffix)
            
    return segments

def set_model_file(model, model_root, file_paths, root, result, extension, key):
    candidates = [file_path for file_path in file_paths if file_path.endswith(extension)]
    
    candidate = "{}{}".format(model,extension)
    
    value = None
        
    if (candidate in candidates):
        value = os.path.join(root,candidate)
    elif (len(candidates)==1):
        value = os.path.join(root,candidates[0])

    if (value):
        rel_path = os.path.relpath(value,model_root)
        
        segments = _split_path(rel_path)[:-1]
        
        segments.append(key)
        
        _set_namespace_value(result, segments, value)


def find_model(model, pipeline_root, args):

    if model == "full_frame":
        return model

    result = SimpleNamespace()
        
    model_root = os.path.join(os.path.join(pipeline_root, "models"), model)

    if (not os.path.isdir(model_root)):
        raise Exception("Can't find model root for: {}".format(model))

    for root, directories, file_paths in os.walk(model_root):

        set_model_file(model, model_root, file_paths, root, result, ".json", "proc")

        set_model_file(model, model_root, file_paths, root, result, ".xml", "xml")

        set_model_file(model, model_root, file_paths, root, result, ".bin", "bin")
            
    return result

def find_pipeline(pipeline, args):
    pipelines_root = args.workspace_root
    pipeline_root = None
    
    for root, directories, files in os.walk(pipelines_root):
        if (pipeline in directories):
            pipeline_root = os.path.abspath(os.path.join(root,pipeline))
            break

    if (not pipeline_root):
        if (os.path.isdir(pipeline)):
            pipeline_root = os.path.abspath(pipeline)

    if (not pipeline_root):
        return None

    file_paths = [ file_path for file_path in os.listdir(pipeline_root)
                   if os.path.isfile(os.path.join(pipeline_root,file_path)) and
                   file_path.endswith(".pipeline.yml")] 

    candidate_filename = "{}.pipeline.yml".format(pipeline)

    if candidate_filename in file_paths:
        return os.path.join(pipeline_root,candidate_filename)

    if len(file_paths)==1:
        return os.path.join(pipeline_root,file_paths[0])
    
    return None


class Task(object, metaclass=abc.ABCMeta):

    task_map = None
    
    @property
    @classmethod
    @abc.abstractmethod
    def names(cls):
        pass

    @abc.abstractmethod
    def __init__(self, task, workload, args):
        pass

    @abc.abstractmethod
    def prepare(self, workload_root, timeout):
        pass

    @classmethod
    def create_task(cls, workload, args):
        if (not cls.task_map):
            cls.task_map = {}
            tasks = [task_class for task_class in Task.__subclasses__()]
            for task in tasks:
                for task_name in task.names:
                    cls.task_map[task_name] = task
                    
        pipeline_path = find_pipeline(workload.pipeline, args)
        if (not pipeline_path):
            raise Exception("Can't find pipeline {}, please make sure it is downloaded!".format(workload.pipeline))
                    
        pipeline = PipelineConfig(pipeline_path, args)

        task = pipeline._task.get_task_scenario(workload._namespace.scenario)

        task_name = pipeline._task.name

        return  cls.task_map[task_name](pipeline, task, workload, args)
        

    
