import os
import time
import subprocess
import shlex
import stat

from tasks.task import Task
from tasks.task import input_to_src
from tasks.task import decode_properties
from tasks.task import vpp_properties
from tasks.task import output_to_sink

class DecodeVPP(Task):
    supported_tasks = ["decode-vpp"]

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

    def _create_standalone_elements(self):

        demux = ( "qtdemux" if os.path.splitext(
            self._piperun_config["inputs"][0]["source"])[1]==".mp4" else "")
        
        return ["urisourcebin uri=file://{}".format(
            self._piperun_config["inputs"][0]["source"]),
                demux,
                "parsebin",
                self._decode_properties,
                self._vpp_properties,
                "gvafpscounter ! multifilesink location=\"%d.bin\""
        ]


    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        self.completed = None
        self._piperun_config = piperun_config
        self._runner_config = self._piperun_config["runner-config"]
        self._runner_config.setdefault("decode", {"device":"CPU"})
        self._runner_config.setdefault("vpp",{"device":"CPU"})
        decode_queue_name = "decode-queue"
        decode_queue_config = self._runner_config.setdefault(decode_queue_name,{})
        vpp_queue_name = "vpp-queue"
        vpp_queue_config = self._runner_config.setdefault(vpp_queue_name,{})
        color_space = self._piperun_config["pipeline"].get("color-space",None)
        region = self._piperun_config["pipeline"].get("region",None)
        resolution = self._piperun_config["pipeline"].get("resolution",None)
        
        self._my_args = args

        if len(self._piperun_config["inputs"]) != 1:
            raise Exception("Only support single input")

        if len(self._piperun_config["outputs"]) != 1:
            raise Exception("Only support single output")

        print(input_to_src)
        self._src_element = input_to_src(self._piperun_config["inputs"][0])

        

        self._decode_properties = decode_properties(self._runner_config["decode"],
                                                    self._runner_config["decode-queue"],
                                                    None,
                                                    self._piperun_config["inputs"][0],
                                                    self._my_args.systeminfo)

        self._vpp_properties = vpp_properties(self._runner_config["vpp"],
                                              vpp_queue_config,
                                              color_space,
                                              region,
                                              resolution,
                                              self._my_args.systeminfo)
                                              
        
        self._sink_element = output_to_sink(self._piperun_config["outputs"][0])
        print(self._src_element)
        print(self._sink_element)
        print(self._decode_properties)

        caps = self._piperun_config["inputs"][0]["caps"]
        
        if ("msdk" in self._decode_properties):
            caps = self._piperun_config["inputs"][0]["extended-caps"]


        self._elements = [self._src_element,
                          caps,
                          self._decode_properties,
                          self._vpp_properties,
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
