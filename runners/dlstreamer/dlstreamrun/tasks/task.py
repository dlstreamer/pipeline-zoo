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

    parser_map = defaultdict(lambda:"parsebin",
                             {"video/x-h264":"h264parse",
                              "video/x-h265":"h265parse"
                             })

    parsed_uri = parse.urlparse(_input["uri"])  
    element = scheme_map[parsed_uri.scheme]
    media_type = _input["caps"].split(",")[0]
    parser = parser_map[media_type]
    
    if (element == "filesrc"):
        element = "filesrc location=\"{}\" ! {} ! {}".format(parsed_uri.path,media_type,parser)
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
        if key == "proc":
            _set_namespace_value(result,["proc"],value)

def find_model(model, models_root, result=None):

    if model == "full_frame":
        return model

    if model.endswith("jsonl"):
        return model

    if (result is None):
        result = SimpleNamespace()
        
    model_root = os.path.join(models_root, model)

    if (not os.path.isdir(model_root)):
        raise Exception("Can't find model root for: {}".format(model))

    for root, directories, file_paths in os.walk(model_root):

        set_model_file(model, model_root, file_paths, root, result, ".json", "proc")

        set_model_file(model, model_root, file_paths, root, result, ".xml", "xml")

        set_model_file(model, model_root, file_paths, root, result, ".bin", "bin")

    int8_model = model + "_INT8"
    int8_model_root = os.path.join(models_root,int8_model)
    if (os.path.isdir(int8_model_root)):
        find_model(int8_model,models_root,result)
            
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
    decode_caps = ""
    
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
    if "caps" in result:
        decode_caps = " ! {}".format(result["caps"])

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

    non_properties = ["element","device","post-proc-caps","caps"]
    properties = ["{}={}".format(key,value) for key,value in result.items() if key not in non_properties]
    
    template = "{} {} {}{}{}".format(result["element"],
                                  " ".join(properties),
                                     decode_caps,
                                     decode_queue_properties,
                                     post_proc)

    return template

def _detections_from_reference(config, model, model_name, systeminfo):
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "add_detections.py")
    
    return "gvapython module={} class=AddDetections arg=[\\\"{}\\\"]".format(module_path,
                                                                             model_name)
        
def inference_properties(config, model, model_name, systeminfo):

    result = config

    if model_name == "full_frame":
        return ""

    if (not result["enabled"]):
        return ""

    if model_name.endswith("jsonl"):
        return _detections_from_reference(config,model,model_name,systeminfo)

    result.setdefault("device","CPU")
    threads = number_of_physical_threads(systeminfo)
    if (getattr(model,"proc",None)):
        result.setdefault("model-proc",model.proc)
    
    if (result["device"]=="CPU"):
        precision = result.setdefault("precision","FP32")

    if (result["device"]=="HDDL"):
        precision = result.setdefault("precision","FP16")

    if ("GPU." in result["device"]):
        precision = result.setdefault("precision","FP32-INT8")

    if (result["device"]=="GPU"):
        precision = result.setdefault("precision","FP16")

    if ("MULTI" in result["device"]):
        precision = result.setdefault("precision","FP16")

    if hasattr(model,precision):
        result.setdefault("model",getattr(model,precision).xml)
    elif list(model.__dict__.keys()):
        default_precision = list(model.__dict__.keys())[0]
        print("\nNo {} Model found, trying: {}\n".format(precision, default_precision))
        result.setdefault("model",getattr(model,default_precision).xml)
    else:
        raise Exception("Can't find precision: {} for model: {}".format(precision,model_name))

    non_properties = ["element","enabled","precision"]
    
    properties = ["{}={}".format(key,value) for key,value in result.items() if key not in non_properties]
    
    template = "{} {}".format(result["element"],
                                     " ".join(properties))

        
    return template
    
class ObjectDetection(Task):

    supported_tasks = ["object-detection"]

    supported_uri_schemes = ["pipe", "file", "rtsp"]
    
    detect_model_config = "model"

    classify_model_config = None
    
    def _set_classify_properties(self, detect_model_name=""):
        result = ""
        elements = []
        if (self.classify_model_config):
            classify_model_list = self._piperun_config["pipeline"][self.classify_model_config]
            for index, model_name in enumerate(classify_model_list):
                if (isinstance(model_name,list)):
                    raise Exception("Dependent Classification Not Supported")
                model = find_model(model_name,
                                   self._piperun_config["models-root"])
                element_name = "classify-{}".format(index)
                classify_config = self._runner_config.setdefault(element_name,
                                                                 {})
                classify_config.setdefault("element","gvaclassify")
                classify_config.setdefault("name",element_name)
                classify_config.setdefault("enabled", True)

                if detect_model_name=="full_frame":
                    classify_config.setdefault("inference-region", "full-frame")

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
                                                     model_name,
                                                     self._my_args.systeminfo))
            if (elements):
                result = " ! ".join([element for element in elements if element])
            
        return result

    def _create_standalone_elements(self):

        demux = ( "qtdemux" if os.path.splitext(
            self._piperun_config["inputs"][0]["source"])[1]==".mp4" else "")
        
        return ["urisourcebin uri=file://{}".format(
            self._piperun_config["inputs"][0]["source"]),
                demux,
                "parsebin",
                self._decode_properties,
                self._detect_queue_properties,
                self._detect_properties,
                self._classify_properties,
                "gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/result.jsonl ! gvafpscounter ! fakesink"
        ]

    
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

        detect_model_name = self._piperun_config["pipeline"][self.detect_model_config]
        
        self._model = find_model(detect_model_name,
                                 self._piperun_config["models-root"])

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
                                                       detect_model_name,
                                                       self._my_args.systeminfo)

        self._runner_config.setdefault("decode", {"device":"CPU"})

        queue_name = "decode-queue"
        queue_config = self._runner_config.setdefault(queue_name,{})

        self._decode_properties = decode_properties(self._runner_config["decode"],
                                                    self._runner_config["decode-queue"],
                                                    self._model,
                                                    self._piperun_config["inputs"][0],
                                                    self._my_args.systeminfo)

        self._classify_properties = self._set_classify_properties(detect_model_name=detect_model_name)

        # "src ! caps ! decode ! detect ! classify ! metaconvert ! metapublish ! sink "

        self._elements = [self._src_element,
                          self._piperun_config["inputs"][0]["caps"],
                          self._decode_properties,
                          self._detect_queue_properties,
                          self._detect_properties,
                          self._classify_properties,
                          self._sink_element]

        standalone_elements = self._create_standalone_elements()

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
            command_file.write("{}\n".format(' '.join(standalone_args).replace('(','\(').replace(')','\)').replace('"','\\"')))
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
            if (time.time()-start > 2):
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
        
