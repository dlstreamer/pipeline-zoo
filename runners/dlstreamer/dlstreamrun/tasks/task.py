'''
* Copyright (C) 2019 Intel Corporation.
*
* SPDX-License-Identifier: MIT
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
import functools

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
        if parsed_uri.path.endswith(".mp4"):
            media_type = "qtdemux"
        element = "filesrc location=\"{}\" ! {} ! {}".format(parsed_uri.path,media_type,parser)
    return element

def output_to_sink(_output,config,channel_number=0, overlay_pipeline=None, run_directory=None):

    parsed_uri = parse.urlparse(_output["uri"])  

    scheme_map = defaultdict(lambda: "file",
                             {"pipe":"file",
                              "file":"file",
                              "mqtt":"mqtt",
                              "kafka":"kafka"})

    media_type_map = defaultdict(None,
                                 {"metadata/objects": "gvametaconvert add-empty-results=true ! gvametapublish {} ! gvafpscounter ! {}",
                                  "metadata/line-per-frame": "gvametaconvert add-empty-results=true ! gvametapublish {} ! {}",
                                  "video/x-raw": "{}"})

    caps = _output["caps"].split(',')
    template = "{}".format(media_type_map[caps[0]])
    sink_path = parsed_uri.path

    if "overlay" in config:
        media_encoder_map = {
            "video/x-h265": {
                "GPU":"vaapih265enc"}}
        encode_caps = config["overlay"].get("caps", "video/x-h265")
        if encode_caps in media_encoder_map:
            device = config["overlay"].get("device")
            overlay_pipeline = "{} ! {} ".format(overlay_pipeline, media_encoder_map[encode_caps][device])
            template = "gvametaconvert add-empty-results=true ! gvametapublish {} ! gvafpscounter ! " + overlay_pipeline + " ! {} "
            sink_path = "{}/channel_{}_output.h265".format(run_directory, channel_number)
    
    sink_name = "sink"+str(channel_number)   
    sink_config = config.setdefault("sink",{})
    if "metadata" in caps[0] and "overlay" not in config:
        sink_config.setdefault("element", "fakesink")
    else:
        sink_config.setdefault("element", "filesink")

    sink_config.setdefault("async","false")
    sink_config["name"] = sink_name
    if sink_config["element"] == 'filesink':
        sink_config.setdefault("location", sink_path)

    sink_properties = " ".join(["{}={}".format(key,value) for key,value in sink_config.items() if key != "element" and key != "enabled"])
    sink = "{} {}".format(sink_config["element"], sink_properties)

    if template and ("metapublish" in template):
    
        method = "method={}".format(scheme_map[parsed_uri.scheme])
        _format = ""
        if "file" in method and "format=jsonl" in caps:
            _format = "file-format={}".format("json-lines")

        path = ""
        if "file" in method:
            path = "file-path={}".format(parsed_uri.path)
        template = template.format(" ".join([method, _format, path]),sink)
    elif template:
        template = template.format(sink)

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

        set_model_file(model, model_root, file_paths, root, result, ".txt", "labels")

    int8_model = model + "_INT8"
    int8_model_root = os.path.join(models_root,int8_model)
    if (os.path.isdir(int8_model_root)):
        find_model(int8_model,models_root,result)
            
    return result

def number_of_physical_threads(systeminfo):
    return systeminfo["cpu"]["NumberOfCPUs"]

def intel_gpu(systeminfo):
    return ("gpu" in systeminfo and "Intel" in systeminfo["gpu"]["Device name"])

@functools.lru_cache
def labels_supported():
    inspect_output = subprocess.check_output(["gst-inspect-1.0", "gvadetect"]).decode("utf-8").strip()
    return "labels" in inspect_output

def queue_properties(config, model, systeminfo):
    result = ""

    if (config["enabled"]):
        properties = ["{}={}".format(key,value) for key,value in config.items() if key != "element" and key != "enabled"]

        result = "{} {}".format(config["element"],
                                  " ".join(properties))
    return result

def vpp_properties(config,
                   queue_config,
                   color_space,
                   region,
                   resolution,
                   systeminfo,
                   channel_number=0):

    elements =[]


    if (config.setdefault("use-msdk", False)):
        config["device"] = "GPU"

    if intel_gpu(systeminfo):
        config.setdefault("device", "GPU")
    else:
        config.setdefault("device", "CPU")

    output_caps = "! video/x-raw"
        
    if config["device"] == "GPU":
        output_caps = "! video/x-raw(memory:VASurface)"
    
    if color_space:
        output_caps += ",format={}".format(color_space.upper())
    if resolution:
        output_caps += ",height={},width={}".format(resolution["height"],
                                                    resolution["width"])

    if config["device"] == "CPU":        
        if region:
            pass
        if resolution:
            video_scale_config = config.setdefault("videoscale", {})
            properties = ["{}={}".format(key,value) for key,value in video_scale_config.items()]
            elements.append("videoscale name={} {}".format("videoscale"+str(channel_number), " ".join(properties)))
        if color_space:
            video_convert_config = config.setdefault("videoconvert",{})
            properties = ["{}={}".format(key,value) for key,value in video_convert_config.items()]
            elements.append("videoconvert name={} {}".format("videoconvert"+str(channel_number), " ".join(properties)))
    elif config["device"] == "GPU":
        post_proc_element = "vaapipostproc"
        
        if config["use-msdk"]:
            post_proc_element = "msdkvpp"
        
        postproc_config = config.setdefault(post_proc_element,{})
        properties = ["{}={}".format(key,value) for key,value in postproc_config.items()]
        elements.append("{} name={} {}".format(post_proc_element,
                                               post_proc_element+str(channel_number),
                                               " ".join(properties)))

    queue_name = "vpp-queue"
    queue_config.setdefault("element", "queue")
    queue_config.setdefault("name", queue_name + str(channel_number))
    queue_config.setdefault("enabled", False)

    vpp_queue_properties = queue_properties(queue_config,
                                            None,
                                            systeminfo)
    if (vpp_queue_properties):
        vpp_queue_properties = " ! {}".format(vpp_queue_properties)

    if elements:
        template = "{} {} {}".format("! ".join(elements),
                                     output_caps,
                                     vpp_queue_properties)
    else:
        template = ""
   
    return template

    

def decode_properties(config, queue_config, _input, systeminfo, channel_number = 0):

    media_type_map = defaultdict(lambda:{"CPU":"decodebin","GPU":"vaapidecodebin"},
                                 {"video/x-h264": {"CPU":"avdec_h264", "GPU":"vaapih264dec"},
                                  "video/x-h265": {"CPU":"avdec_h265", "GPU":"vaapih265dec"}})
    if (config.setdefault("use-msdk", False)):
        media_type_map = defaultdict(lambda:{"CPU":None,"GPU":None},
                                 {"video/x-h264": {"CPU":None, "GPU":"msdkh264dec"},
                                  "video/x-h265": {"CPU":None, "GPU":"msdkh265dec"}})
        config["device"] = "GPU"
        
    
    result = config
    post_proc = ""
    decode_caps = ""
    
    if intel_gpu(systeminfo):
        result.setdefault("device", "GPU")
    else:
        result.setdefault("device", "CPU")

    media_type = _input["caps"].split(",")[0]

    result.setdefault("element",media_type_map[media_type][result["device"]])
    result.setdefault("name", "decode" + str(channel_number))

    if result["element"] in ["vaapih264dec","vaapih265dec","msdkh264dec","msdkh265dec"]:
        if ("max-threads" in result):
            result.pop("max-threads")
    if "caps" in result:
        decode_caps = " ! {}".format(result["caps"])

    if "post-proc-caps" in result:
        if result["device"] == "GPU":
            post_proc = " ! vaapipostproc ! {}".format(result["post-proc-caps"])
            if result["use-msdk"]:
                post_proc = post_proc.replace("vaapipostproc", "msdkvpp")
        elif result["device"] == "CPU":
            post_proc = " ! videoscale ! videoconvert ! {}".format(result["post-proc-caps"])

    queue_name = "decode-queue"
    queue_config.setdefault("element", "queue")
    queue_config.setdefault("name", queue_name+str(channel_number))
    queue_config.setdefault("enabled", False)

    decode_queue_properties = queue_properties(queue_config,
                                               None,
                                               systeminfo)
    if (decode_queue_properties):
        decode_queue_properties=" ! {}".format(decode_queue_properties)

    non_properties = ["element","device","post-proc-caps","caps","use-msdk"]
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

    post_proc = ""

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
    if (getattr(model,"labels",None) and labels_supported()):
        result.setdefault("labels",model.labels)
    
    if (result["device"]=="CPU"):
        precision = result.setdefault("precision","FP32")

    if (result["device"]=="HDDL"):
        precision = result.setdefault("precision","FP16")

    if ("GPU." in result["device"]):
        precision = result.setdefault("precision","FP32-INT8")
        post_proc = " ! vaapipostproc !"

    if (result["device"]=="GPU"):
        precision = result.setdefault("precision","FP16")

    if ("MULTI" in result["device"]):
        precision = result.setdefault("precision","FP16")

    if hasattr(model,precision):
        result.setdefault("model",getattr(model,precision).xml)
    else:
        model_precisions = list(filter(lambda x: (x != 'labels' and x != 'proc'), model.__dict__.keys()))
        if model_precisions:
            default_precision = model_precisions[0]
            print("\nNo {} Model found, trying: {}\n".format(precision, default_precision))
            result.setdefault("model",getattr(model,default_precision).xml)
        else:
            raise Exception("Can't find precision: {} for model: {}".format(precision,model_name))

    non_properties = ["element","enabled","precision"]
    
    properties = ["{}={}".format(key,value) for key,value in result.items() if key not in non_properties]
    
    template = "{} {}{}".format(result["element"],
                                     " ".join(properties), post_proc)

        
    return template
    
            
def overlay_properties(config, queue_config, _input, systeminfo, channel_number = 0):
    overlay_element_map = defaultdict(None, {
        "GPU": "meta_overlay device=GPU", 
        "CPU": "meta_overlay device=CPU"})
    overlay_element = overlay_element_map[config["device"]]
    queue_name = "overlay-queue"
    queue_config.setdefault("element", "queue")
    queue_config.setdefault("name", queue_name+str(channel_number))
    queue_config.setdefault("enabled", True)

    encode_queue_properties = queue_properties(queue_config,
                                               None,
                                               systeminfo)
    if (encode_queue_properties):
        encode_queue_properties="{} ! ".format(encode_queue_properties)
    template = "{} {}".format(encode_queue_properties,
                                     overlay_element)

    return template
