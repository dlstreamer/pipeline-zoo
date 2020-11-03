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

class Task(threading.Thread, metaclass=abc.ABCMeta):

    task_map = None
    
    @property
    @classmethod
    @abc.abstractmethod
    def names(cls):
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
            tasks = [task_class for task_class in Task.__subclasses__()]
            for task in tasks:
                for task_name in task.names:
                    cls.task_map[task_name] = task
                                        
        task_name = piperun_config["pipeline"]["task"]

        return  cls.task_map[task_name](piperun_config, args, *pos_args, **keywd_args)



class ObjectDetection(Task):

    names = ["object-detection"]

    caps_to_extension = {"video/x-h264":"x-h264.bin",
                         "metadata/objects":"objects.jsonl"}

    supported_uri_schemes = ["pipe","file"]
    
    def _load_input_sizes(self):

        input_caps = self._piperun_config["inputs"][0]["caps"].split(',')

        extension = self.caps_to_extension[input_caps[0]]
            
        input_path = os.path.join(self._piperun_config["runner-config"]["workload_root"],
                                  "input")

        input_paths = [ os.path.join(input_path,path) for path in os.listdir(input_path)
                        if path.endswith(extension) ]

        input_paths.sort()
        
        input_sizes = [ os.path.getsize(path) for path in input_paths if os.path.isfile(path) ]

        return input_sizes

    def _load_reference(self):
    
        reference_path = os.path.join(self._piperun_config["runner-config"]["workload_root"],
                                      self._piperun_config["runner-config"]["reference"])

        reference = []
        try:
            with open(reference_path,"r") as reference_file:
                for result in reference_file:
                    try:
                        reference.append(json.loads(result))
                    except Exception as error:
                        print(error)
        except Exception as error:
            print("Can't load reference! {}".format(error))
            
        return reference

    
    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        self._piperun_config = piperun_config
        self._args = args
        self._outputs = self._load_reference()
        self._input_sizes = self._load_input_sizes()
        
        if ( len(self._piperun_config["inputs"])!=1):
            raise Exception("Only support single input")

        if ( len(self._piperun_config["outputs"])!=1):
            raise Exception("Only support single input")

        uri = self._piperun_config["inputs"][0]["uri"]
        parsed_uri = parse.urlparse(uri)

        if (not parsed_uri.scheme in self.supported_uri_schemes):
            raise Exception("input scheme {} not supported".format(parsed_uri.scheme))

        self._input_path = parsed_uri.path

        uri = self._piperun_config["outputs"][0]["uri"]
        parsed_uri = parse.urlparse(uri)

        if (not parsed_uri.scheme in self.supported_uri_schemes):
            raise Exception("output scheme {} not supported".format(parsed_uri.scheme))

        self._output_path = parsed_uri.path
        
        super().__init__(piperun_config, args,*pos_args,**keywd_args)
        
    def run(self):
        count = 0
        input_len = len(self._input_sizes)
        output_len = len(self._outputs)
        assert(input_len == output_len)
        with open(self._input_path,"rb") as input_fifo:
            print("connected to input")
            with open(self._output_path,"wb",buffering = 0 ) as output_fifo:
                print("connected to output")
                # read input frame
                while(True):
                    bytes_read = 0
                    frame_size = self._input_sizes[count %input_len]
                    while(bytes_read<frame_size):                
                        print(frame_size)
                        bytes_read += len(input_fifo.read(frame_size-bytes_read))
                        if (not bytes_read):
                            break
                        print(bytes_read)

                    if (bytes_read):
                        count+=1
                        print("received frame: {}".format(count))
                        print("writing output: {}".format(count))
                        output_fifo.write(bytes("{}\n".format(json.dumps(self._outputs[count%output_len])),"utf-8"))
                    else:
                        return
        
            
class ObjectClassification(ObjectDetection, Task):
    names = ["object-classification"]

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        super().__init__(piperun_config, args,*pos_args,**keywd_args)
