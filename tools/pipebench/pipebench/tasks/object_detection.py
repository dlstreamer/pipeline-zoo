'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
import os
import shutil
from pipebench.util import create_directory
from pipebench.util import print_action
from pipebench.tasks.task import Task
from pipebench.tasks.media_util import create_encoded_frames
import pipebench.tasks.media_util as media_util
from .media_util import create_reference
from .media_util import find_media
from .media_util import read_caps
from pipebench.tasks.media_util import MediaSink
from pipebench.tasks.media_util import MediaSource
from .task import find_model
from types import SimpleNamespace
import yaml
import time
import uuid
from .runner_util import start_pipeline_runner
from threading import Thread
import time

class ObjectDetection(Task):

    names = ["object-detection"]
    OUTPUT_CAPS = "metadata/objects,format=jsonl"
    caps_to_extension = {"video/x-h264":"x-h264.bin"}
    
    def __init__(self, pipeline, task, workload, args):
        self._workload = workload
        self._task = task
        self._pipeline = pipeline
        self._args = args
        self._fps_stats = None
            
    def _create_piperun_config(self, run_root, runner_config):
        piperun_config = {"pipeline":self._pipeline._document}
        filename = "{}.piperun.yml".format(self._args.workload_name)
        pipe_uuid = uuid.uuid1()
        pipe_directory = os.path.join("/tmp",str(pipe_uuid))
        create_directory(pipe_directory)

        self._input_caps = read_caps(os.path.join(self._args.workload_root,"input"))["caps"]
        self._input_path = "{}/input".format(pipe_directory)
        self._input_uri = "pipe://{}".format(self._input_path)
        input = {"uri":self._input_uri,
                 "caps":self._input_caps}

        self._output_caps = ObjectDetection.OUTPUT_CAPS
        self._output_path = "{}/output".format(pipe_directory)
        self._output_uri = "pipe://{}".format(self._output_path)
        output = {"uri":self._output_uri,
                  "caps":self._output_caps}
        
        piperun_config["inputs"] = [input]
        piperun_config["outputs"] = [output]
        piperun_config["config"] = runner_config
        
        piperun_config_path = os.path.join(run_root,filename)

        if (self._args.runner == "mockrun"):
            runner_config["workload_root"] = self._args.workload_root

        runner_config["models_root"] = os.path.join(self._pipeline.pipeline_root,"models")

        if (not self._args.force) and (os.path.isfile(piperun_config_path)):
            return
        
        with open(piperun_config_path,"w") as piperun_config_file:
            yaml.dump(piperun_config,
                      piperun_config_file,
                      sort_keys=False)
            
        return piperun_config_path

                               
    def run(self,
            run_root,
            runner_config,
            warm_up,
            frame_rate,
            sample_size):
        
        # create piperun config
        piperun_config_path = self._create_piperun_config(run_root, runner_config)

        try:
            os.unlink(self._input_path)
            os.unlink(self._output_path)
        except:
            pass

        os.mkfifo(self._input_path)
        os.mkfifo(self._output_path)
        
        # start read thread
        sink = MediaSink(self._output_path,
                         self._output_uri,
                         self._output_caps,
                         warm_up = warm_up,
                         sample_size = sample_size,
                         daemon=True)
        sink.start()
        
        
        runner_process = start_pipeline_runner(self._args.runner,
                                               runner_config,
                                               run_root,
                                               piperun_config_path,
                                               self._pipeline.pipeline_root,
                                               os.path.join(self._args.workload_root,"systeminfo.json"),
                                               redirect=self._args.redirect)
        

        # start writer thread
        
        source = MediaSource(self._input_path,
                             self._input_uri,
                             self._input_caps,
                             elapsed_time = -1,
                             frame_rate = frame_rate,
                             input_directory=os.path.join(self._args.workload_root,"input"),daemon=True)
        source.start()

        
        return source, sink, runner_process

        
        
    def prepare(self, workload_root):
        
        # todo resolve properties of task by filling in details from pipeline

        input_media_type = getattr(self._pipeline._namespace,"inputs.media.type.media-type")

        input_media = find_media(self._workload.media,self._pipeline.pipeline_root,self._args)

        input_target = os.path.join(workload_root, "input")

        if (self._args.force):
            create_directory(input_target)
        
        existing_files = [ file_path for file_path in os.listdir(input_target)
                           if os.path.isfile(os.path.join(input_target,file_path)) ]

        if (existing_files):
            print("Existing input, skipping generation")
        else:
            create_encoded_frames(input_target,
                                  input_media_type,
                                  input_media)
                                
        model_name = self._pipeline._namespace.model


        model = find_model(model_name,
                           self._pipeline.pipeline_root,
                           self._args)
        
        models = SimpleNamespace()
        models.detect = []
        models.detect.append(model)

        reference_target = os.path.join(workload_root, "reference")

        # Todo: get from task document
        output_media_type = "metadata/objects"


        existing_files = [ file_path for file_path in os.listdir(reference_target)
                           if os.path.isfile(os.path.join(reference_target,file_path)) ]

        if (existing_files):
            print("Existing reference, skipping generation")
        else:
            create_reference(input_target,
                             reference_target,
                             output_media_type,
                             models)





