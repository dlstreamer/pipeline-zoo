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
import os, stat
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

def queue_properties(config, model, systeminfo):
    result = ""

    if (config["enabled"]):
        properties = ["{}={}".format(key,value) for key,value in config.items() if key != "element" and key != "enabled"]

        result = "{} {}".format(config["element"],
                                  " ".join(properties))
    return result

def decode_properties(config, queue_config, model, _input, systeminfo):

    media_type_map = defaultdict(lambda:{"CPU":"decodebin","GPU":"vaapidecodebin"},
                                 {"video/x-h264": {"CPU":"avdec_h264", "GPU":"vaapih264dec"}})

    result = config
    post_proc = ""
    if intel_gpu(systeminfo):
        result.setdefault("device", "GPU")
    else:
        result.setdefault("device", "CPU")

    media_type = _input["caps"].split(",")[0]

    result.setdefault("element",media_type_map[media_type][result["device"]])
    result.setdefault("name", "decode")

    if result["element"]=="vaapih264dec":
        if ("max-threads" in result):
            result.pop("max-threads")

    if "post-proc-caps" in result:
        if result["device"] == "GPU":
            post_proc = " ! vaapipostproc ! {}".format(result["post-proc-caps"])
        elif result["device"] == "CPU":
            post_proc = " ! videoconvert ! videoscale ! {}".format(result["post-proc-caps"])

    queue_name = "decode-queue"
    queue_config.setdefault("element", "queue")
    queue_config.setdefault("name", queue_name)
    queue_config.setdefault("enabled", False)

    decode_queue_properties = queue_properties(queue_config,
                                               None,
                                               systeminfo)
    if (decode_queue_properties):
        decode_queue_properties=" ! {}".format(decode_queue_properties)
    properties = ["{}={}".format(key,value) for key,value in result.items() if key != "element" and key!="device" and key!="post-proc-caps"]
    
    template = "{} {} {}{}".format(result["element"],
                                  " ".join(properties),
                                  decode_queue_properties,
                                  post_proc)

    return template



        
def inference_properties(config, model, systeminfo):

    result = config

    if (not result["enabled"]):
        return ""

    result.setdefault("device","CPU")
    threads = number_of_physical_threads(systeminfo)

    if (getattr(model,"proc",None)):
        result.setdefault("model-proc",model.proc)
    
    if (result["device"]=="CPU"):
        #result.setdefault("nireq", threads + 1)
        #result.setdefault("cpu-throughput-streams",threads)
        result.setdefault("model",model.FP32.xml)

    if (result["device"]=="HDDL"):
        result.setdefault("model",model.FP16.xml)

    if (result["device"]=="GPU"):
        result.setdefault("model",model.FP16.xml)

    if ("MULTI" in result["device"]):
        result.setdefault("model",model.FP16.xml)

    
    properties = ["{}={}".format(key,value) for key,value in result.items() if key != "element" and key != "enabled"]
    
    template = "{} {}".format(result["element"],
                                     " ".join(properties))

        
    return template
    
class ObjectDetection(Task):

    supported_tasks = ["object-detection"]

    caps_to_extension = {"video/x-h264":"x-h264.bin",
                         "metadata/objects":"objects.jsonl"}

    supported_uri_schemes = ["pipe", "file", "rtsp"]
    
    detect_model_config = "model"

    classify_model_config = None
    
    def _set_classify_properties(self):
        result = ""
        elements = []
        if (self.classify_model_config):
            classify_model_list = self._piperun_config["pipeline"][self.classify_model_config]
            for index, model_name in enumerate(classify_model_list):
                if (isinstance(model_name,list)):
                    raise Exception("Dependent Classification Not Supported")
                model = find_model(model_name,
                                   self._runner_config["models_root"])
                element_name = "classify-{}".format(index)
                classify_config = self._runner_config.setdefault(element_name,
                                                                 {})
                classify_config.setdefault("element","gvaclassify")
                classify_config.setdefault("name",element_name)
                classify_config.setdefault("enabled", True)

                queue_name = "classify-{}-queue".format(index)
                queue_config = self._runner_config.setdefault(queue_name,{})
                queue_config.setdefault("element", "queue")
                queue_config.setdefault("name", queue_name)
                queue_config.setdefault("enabled", classify_config["enabled"])
                
                elements.append(queue_properties(queue_config,
                                                 model,
                                                 self._my_args.systeminfo))
                elements.append(inference_properties(classify_config,
                                                     model,
                                                     self._my_args.systeminfo))
            if (elements):
                result = " ! ".join([element for element in elements if element])
            
        return result
    
    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        self._piperun_config = piperun_config
        self._my_args = args
        if len(self._piperun_config["inputs"]) != 1:
            raise Exception("Only support single input")

        if len(self._piperun_config["outputs"]) != 1:
            raise Exception("Only support single output")


        self._src_element = input_to_src(self._piperun_config["inputs"][0])
        self._sink_element = output_to_sink(self._piperun_config["outputs"][0])
        self._runner_config = self._piperun_config["runner-config"]
                
        self._model = find_model(self._piperun_config["pipeline"][self.detect_model_config],
                                 self._runner_config["models_root"])

        self._runner_config.setdefault("detect",{})
        self._runner_config["detect"].setdefault("element","gvadetect")
        self._runner_config["detect"].setdefault("name","detect")
        self._runner_config["detect"].setdefault("enabled",True)

        queue_name = "detect-queue"
        queue_config = self._runner_config.setdefault(queue_name,{})
        queue_config.setdefault("element", "queue")
        queue_config.setdefault("name", queue_name)
        queue_config.setdefault("enabled", False)
        
        self._detect_queue_properties = queue_properties(queue_config,
                                                         self._model,
                                                         self._my_args.systeminfo)
        
        self._detect_properties = inference_properties(self._runner_config["detect"],
                                                       self._model,
                                                       self._my_args.systeminfo)

        self._runner_config.setdefault("decode", {"device":"CPU"})

        queue_name = "decode-queue"
        queue_config = self._runner_config.setdefault(queue_name,{})

        self._decode_properties = decode_properties(self._runner_config["decode"],
                                                    self._runner_config["decode-queue"],
                                                    self._model,
                                                    self._piperun_config["inputs"][0],
                                                    self._my_args.systeminfo)

        self._classify_properties = self._set_classify_properties()

        # "src ! caps ! decode ! detect ! classify ! metaconvert ! metapublish ! sink "

        self._elements = [self._src_element,
                          self._piperun_config["inputs"][0]["caps"],
                          self._decode_properties,
                          self._detect_queue_properties,
                          self._detect_properties,
                          self._classify_properties,
                          self._sink_element]

        standalone_elements = ["urisourcebin uri=file://{}".format(self._piperun_config["inputs"][0]["source"]),
                               "qtdemux",
                               "parsebin",
                               self._decode_properties,
                               self._detect_queue_properties,
                               self._detect_properties,
                               self._classify_properties,
                               "gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/result.jsonl ! gvafpscounter ! fakesink"
        ]
                                                                   
                               

        elements = " ! ".join([element for element in self._elements if element])
        standalone_elements = " ! ".join([element for element in standalone_elements if element])
        command = "gst-launch-1.0 " + elements
        standalone_command = "gst-launch-1.0 " + standalone_elements
        self._commandargs = shlex.split(command)
        standalone_args = shlex.split(standalone_command)
        dirname, basename = os.path.split(self._my_args.piperun_config_path)
        command_path = os.path.join(dirname,
                                 basename.replace('piperun.yml',"gst-launch.sh"))
        with open(command_path,"w") as command_file:
            command_file.write("{}\n".format(' '.join(standalone_args).replace('(','\(').replace(')','\)')))
        os.chmod(command_path,stat.S_IXGRP | stat.S_IXOTH | stat.S_IEXEC | stat.S_IWUSR | stat.S_IROTH | stat.S_IRUSR)
        self.completed = None
        super().__init__(piperun_config, args, *pos_args, **keywd_args)

        
    def run(self):
        print(' '.join(self._commandargs))
        print("\n\n", flush=True)
        launched = False
        max_attempts = 5
        completed = None
        while ((not launched) and max_attempts):
            start = time.time()
            completed = subprocess.run(self._commandargs)
            if (time.time()-start > 10):
                launched = True
            else:
                max_attempts -= 1
        self.completed = completed
            
class ObjectClassification(ObjectDetection, Task):
    supported_tasks = ["object-classification"]

    detect_model_config = "detection-model"

    classify_model_config = "classification-models"

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        super().__init__(piperun_config, args, *pos_args, **keywd_args)
        
