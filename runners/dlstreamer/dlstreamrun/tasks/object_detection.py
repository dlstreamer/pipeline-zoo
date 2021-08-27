import os
import stat
import time
import shlex
import subprocess
from tasks.task import Task
from tasks.task import input_to_src
from tasks.task import decode_properties
from tasks.task import output_to_sink
from tasks.task import find_model
from tasks.task import queue_properties
from tasks.task import inference_properties


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

        caps = self._piperun_config["inputs"][0]["caps"]
        
        if ("msdk" in self._decode_properties):
            caps = self._piperun_config["inputs"][0]["extended-caps"]
        
        self._elements = [self._src_element,
                          caps,
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
