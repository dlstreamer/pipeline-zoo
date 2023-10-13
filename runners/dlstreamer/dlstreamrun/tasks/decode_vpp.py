import os
import time
import subprocess
import shlex
import stat
import copy

from tasks.task import Task
from tasks.channel import Channel

class DecodeVPP(Task):
    supported_tasks = ["decode-vpp"]

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        self._piperun_config = piperun_config
        self._my_args = args

        super().__init__(piperun_config, args, *pos_args, **keywd_args)
        self.create_channels()
        self.create_command()

    def create_channels(self):
        self._channels = []
        color_space = self._piperun_config["pipeline"].get("color-space",None)
        region = self._piperun_config["pipeline"].get("region",None)
        resolution = self._piperun_config["pipeline"].get("resolution",None)

        for i in range(len(self._piperun_config["inputs"])):
            caps = self._piperun_config["inputs"][i]["caps"]

            channel = Channel(copy.deepcopy(self._piperun_config["runner-config"]), None, self._my_args.systeminfo, caps, i)
            channel.add_src_element(self._piperun_config["inputs"][i])
            channel.add_caps_element(caps)
            channel.add_decode_element()
            channel.add_vpp_element(color_space, region, resolution)
            channel.add_sink_element(self._piperun_config["outputs"][i])
            channel.add_fpscounter_element()
            channel.add_multifilesink_element()

            self._channels.append(channel)

    def create_command(self):
        elements = ""
        standalone_elements = ""

        for channel in self._channels:
            standalone_elements = standalone_elements + channel.get_channel_standalone_pipeline() + " "
            elements = elements + channel.get_channel_pipeline() + " "

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
