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
    def __init__(self, piperun_config, args,stream_index, *pos_args,**keywd_args):
        super().__init__(*pos_args,**keywd_args)

    @abc.abstractmethod
    def run(self):
        pass

    @classmethod
    def create_task(cls, piperun_config, args, stream_index,*pos_args,**keywd_args):
        if (not cls.task_map):
            cls.task_map = {}
            tasks = [task_class for task_class in Task.__subclasses__()]
            for task in tasks:
                for task_name in task.names:
                    cls.task_map[task_name] = task
                                        
        task_name = piperun_config["pipeline"]["task"]

        return  cls.task_map[task_name](piperun_config, args, stream_index, *pos_args, **keywd_args)



class ObjectDetection(Task):

    names = ["object-detection"]

    caps_to_extension = {"video/x-h264":"x-h264.bin",
                         "metadata/objects":"objects.jsonl",
                         "video/x-raw":"raw.bin"}
    
    supported_uri_schemes = ["pipe","file"]
    
    def _load_input_sizes(self):

        input_caps = self._piperun_config["inputs"][self._stream_index]["caps"].split(',')

        extension = self.caps_to_extension[input_caps[0]]
            
        input_path = os.path.join(self._piperun_config["runner-config"]["workload-root"],
                                  "input")

        input_paths = [ os.path.join(input_path,path) for path in os.listdir(input_path)
                        if path.endswith(extension) ]

        input_paths.sort()
        
        input_sizes = [ os.path.getsize(path) for path in input_paths if os.path.isfile(path) ]

        return input_sizes

    def _load_reference(self):

        output_caps = self._piperun_config["outputs"][self._stream_index]["caps"].split(',')

        extension = self.caps_to_extension[output_caps[0]]

    
        reference_path = os.path.join(self._piperun_config["runner-config"]["workload-root"],
                                      "reference")

        reference_paths = [ os.path.join(reference_path,path) for path in os.listdir(reference_path)
                            if path.endswith(extension) ]
        
        reference_paths.sort()

        reference = []
        
        try:
            if extension.endswith("jsonl"):
                for path in reference_paths:
                    if os.path.basename(path)!="objects.jsonl":
                        continue
                    with open(path,"r") as reference_file:
                        for result in reference_file:
                            try:
                                reference.append(json.loads(result))
                            except Exception as error:
                                print(error)
            else:
                for path in reference_paths:
                    with open(path,"rb") as reference_file:
                        reference.append(reference_file.read())
        except Exception as error:
            print("Can't load reference! {}".format(error))
            
        return reference

    
    def __init__(self, piperun_config, args, stream_index, *pos_args, **keywd_args):
        self._piperun_config = piperun_config
        self._args = args
        self._stream_index = stream_index
        self._outputs = self._load_reference()
        self._input_sizes = self._load_input_sizes()

        uri = self._piperun_config["inputs"][stream_index]["uri"]
        parsed_uri = parse.urlparse(uri)

        if (not parsed_uri.scheme in self.supported_uri_schemes):
            raise Exception("input scheme {} not supported".format(parsed_uri.scheme))

        self._input_path = parsed_uri.path

        uri = self._piperun_config["outputs"][stream_index]["uri"]
        parsed_uri = parse.urlparse(uri)
        
        if (not parsed_uri.scheme in self.supported_uri_schemes):
            raise Exception("output scheme {} not supported".format(parsed_uri.scheme))

        self._output_path = parsed_uri.path
        
        super().__init__(piperun_config, args,stream_index, *pos_args,**keywd_args)
        
    def run(self):
        count = 0
        input_len = len(self._input_sizes)
        output_len = len(self._outputs)
        print(input_len)
        print(output_len)
        assert(input_len == output_len)
        output_caps = self._piperun_config["outputs"][self._stream_index]["caps"].split(',')
        extension = self.caps_to_extension[output_caps[0]]

        with open(self._input_path,"rb") as input_fifo:
            print("connected to input stream: {}".format(self._stream_index))
            with open(self._output_path,"wb",buffering = 0 ) as output_fifo:
                print("connected to output stream: {}".format(self._stream_index))
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
                        print("received frame: {} stream: {}".format(count,self._stream_index))
                        print("writing output: {} stream: {}".format(count,self._stream_index))
                        if extension.endswith("jsonl"):
                            output_fifo.write(bytes("{}\n".format(json.dumps(self._outputs[count%output_len])),"utf-8"))
                        else:
                            output_fifo.write(self._outputs[count%output_len])
                    else:
                        return
        
            
class ObjectClassification(ObjectDetection, Task):
    names = ["object-classification"]

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        super().__init__(piperun_config, args,*pos_args,**keywd_args)


class DecodeVPP(ObjectDetection, Task):
    names = ["decode-vpp"]

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        super().__init__(piperun_config, args, *pos_args,**keywd_args)
