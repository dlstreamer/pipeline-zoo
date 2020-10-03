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
import os
import threading
import time
from urllib import parse
from collections import defaultdict
import shlex
import subprocess

def input_to_src(_input):

    scheme_map = defaultdict(lambda: "urisrcbin",
                             {"pipe":"filesrc",
                              "file":"filesrc",
                              "rtsp":"rtspsrc"})

    parsed_uri = parse.urlparse(_input["uri"])  
    element = scheme_map[parsed_uri.scheme]

    if (element == "filesrc"):
        element = "filesrc location=\"{}\" ! video/x-h264 ! h264parse".format(parsed_uri.path)
    return element

def output_to_sink(_output):

    parsed_uri = parse.urlparse(_output["uri"])  

    scheme_map = defaultdict(lambda: "file",
                             {"pipe":"file",
                              "file":"file",
                              "mqtt":"mqtt",
                              "kafka":"kafka"})

    media_type_map = defaultdict(None,
                           {"metadata/objects": "gvametaconvert add-empty-results=true ! gvametapublish {} ! gvafpscounter ! fakesink"})

    caps = _output["caps"].split(',')
    
    template = media_type_map[caps[0]]

    if template and ("metapublish" in template):
    
        method = "method={}".format(scheme_map[parse.urlparse(_output["uri"]).scheme])
        _format = ""
        if "file" in method and "format=jsonl" in caps:
            _format = "file-format={}".format("json-lines")

        path = ""
        if "file" in method:
            path = "file-path={}".format(parsed_uri.path)
        template = template.format(" ".join([method, _format, path]))

    return template
    


URI_SCHEME_TO_SINK_ELEMENT = defaultdict(lambda: "fakesink",
                                         {"pipe":"metapublish ! fakesink",
                                          "file":"filesrc",
                                          "rtsp":"rtspsrc"})


class Task(threading.Thread, metaclass=abc.ABCMeta):

    task_map = None
    
    @property
    @classmethod
    @abc.abstractmethod
    def supported_tasks(cls):
        pass

    @abc.abstractmethod
    def __init__(self, piperun_config, args,*pos_args,**keywd_args):
        super().__init__(*pos_args,**keywd_args)

    @abc.abstractmethod
    def run(self):
        pass

    @classmethod
    def create_task(cls, piperun_config, args, *pos_args,**keywd_args):
        if (not cls.task_map):
            cls.task_map = {}
            task_classes = [task_class for task_class in Task.__subclasses__()]
            for task_class in task_classes:
                for task_name in task_class.supported_tasks:
                    cls.task_map[task_name] = task_class
                                        
        task_name = piperun_config["pipeline"]["task"]

        return  cls.task_map[task_name](piperun_config, args, *pos_args, **keywd_args)


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
        value = os.path.join(root, candidate)
    elif (len(candidates)==1):
        value = os.path.join(root, candidates[0])

    if (value):
        rel_path = os.path.relpath(value,model_root)
        
        segments = _split_path(rel_path)[:-1]
        
        segments.append(key)
        
        _set_namespace_value(result, segments, value)

def find_model(model, models_root):

    result = SimpleNamespace()
        
    model_root = os.path.join(models_root, model)

    if (not os.path.isdir(model_root)):
        raise Exception("Can't find model root for: {}".format(model))

    for root, directories, file_paths in os.walk(model_root):

        set_model_file(model, model_root, file_paths, root, result, ".json", "proc")

        set_model_file(model, model_root, file_paths, root, result, ".xml", "xml")

        set_model_file(model, model_root, file_paths, root, result, ".bin", "bin")
            
    return result

def number_of_physical_threads(systeminfo):
    return systeminfo["cpu"]["NumberOfCPUs"]

def intel_gpu(systeminfo):
    return ("gpu" in systeminfo and "Intel" in systeminfo["gpu"]["Device name"])

def decode_properties(config, model, _input, systeminfo):

    media_type_map = defaultdict(lambda:{"CPU":"decodebin","GPU":"vaapidecodebin"},
                                 {"video/x-h264": {"CPU":"avdec_h264", "GPU":"vaapih264dec"}})

    result = config
    
    if intel_gpu(systeminfo):
        result.setdefault("device", "GPU")
    else:
        result.setdefault("device", "CPU")

    media_type = _input["caps"].split(",")[0]

    result.setdefault("element",media_type_map[media_type][result["device"]])
    result.setdefault("name", "decode")

    if result["element"]=="vaapih264dec":
        result.setdefault("low-latency", "true")

    if result["element"]=="avdec_h264":
        result.setdefault("max-threads", "1")

    properties = ["{}={}".format(key,value) for key,value in result.items() if key != "element" and key!="device"]
    
    template = "{} {}".format(result["element"],
                                     " ".join(properties))

    return template
       
def inference_properties(config, model, systeminfo):

    result = config

    result.setdefault("device","CPU")
    threads = number_of_physical_threads(systeminfo)

    result.setdefault("model-proc",model.proc)

    
    if (result["device"]=="CPU"):
        result.setdefault("nireq", threads + 1)
        result.setdefault("cpu-throughput-streams",threads)
        result.setdefault("model",model.FP32.xml)

    properties = ["{}={}".format(key,value) for key,value in result.items() if key != "element" and key!="device"]
    
    template = "{} {}".format(result["element"],
                                     " ".join(properties))

        
    return template
    
class ObjectDetection(Task):

    supported_tasks = ["object-detection"]

    caps_to_extension = {"video/x-h264":"x-h264.bin",
                         "metadata/objects":"objects.jsonl"}

    supported_uri_schemes = ["pipe", "file", "rtsp"]
    
      
    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        self._piperun_config = piperun_config
        self._args = args
      
        if len(self._piperun_config["inputs"]) != 1:
            raise Exception("Only support single input")

        if len(self._piperun_config["outputs"]) != 1:
            raise Exception("Only support single output")


        self._src_element = input_to_src(self._piperun_config["inputs"][0])
        self._sink_element = output_to_sink(self._piperun_config["outputs"][0])

        self._model = find_model(self._piperun_config["pipeline"]["model"],
                                 self._piperun_config["config"]["models_root"])


        self._piperun_config.setdefault("detect",{})
        self._piperun_config["detect"].setdefault("element","gvadetect")
        self._piperun_config["detect"].setdefault("name","detect")
        self._detect_properties = inference_properties(self._piperun_config["detect"],
                                                       self._model,
                                                       self._args.systeminfo)

        self._piperun_config.setdefault("decode", {"device":"CPU"})
        self._decode_properties = decode_properties(self._piperun_config["decode"],
                                                    self._model,
                                                    self._piperun_config["inputs"][0],
                                                    self._args.systeminfo)


        # "src ! caps ! decode ! detect ! metaconvert ! metapublish ! sink "

        self._elements = [self._src_element,
                          self._piperun_config["inputs"][0]["caps"],
                          self._decode_properties,
                          self._detect_properties,
                          self._sink_element]
                
        
        super().__init__(piperun_config, args,*pos_args,**keywd_args)
        
    def run(self):
        
        elements = " ! ".join(self._elements)
        command = "gst-launch-1.0 " + elements
        commandargs = shlex.split(command)
        print(' '.join(commandargs))
        with subprocess.Popen(commandargs) as process:
            pass
        
        
    
            
