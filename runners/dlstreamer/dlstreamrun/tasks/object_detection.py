import os
import stat
import time
import shlex
import subprocess
import copy
from tasks.task import Task
from tasks.channel import Channel

class ObjectDetection(Task):

    supported_tasks = ["object-detection"]

    supported_uri_schemes = ["pipe", "file", "rtsp"]

    detect_model_config = "model"

    classify_model_config = None

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        self._piperun_config = piperun_config
        self._my_args = args
        self.run_directory = os.path.dirname(args.piperun_config_path)
        self.overlay_pipeline = None

        super().__init__(piperun_config, args, *pos_args, **keywd_args)
        self.create_channels()
        self.create_command()

    def create_channels(self):
        detect_model_name = self._piperun_config["pipeline"][self.detect_model_config]

        self._channels = []

        classify_model_config = None

        if self.classify_model_config:
            classify_model_config = self._piperun_config["pipeline"][self.classify_model_config]

        for i in range(len(self._piperun_config["inputs"])):
            caps = self._piperun_config["inputs"][i]["caps"]

            channel = Channel(copy.deepcopy(self._piperun_config["runner-config"]), self._piperun_config["models-root"], self._my_args.systeminfo, caps, i)

            channel.add_src_element(self._piperun_config["inputs"][i])
            channel.add_caps_element(caps)
            channel.add_decode_element()
            channel.add_detect_element(detect_model_name)
            if "barcode_detector" in self._piperun_config["runner-config"]:
                channel.add_barcode_detector_element(self._piperun_config["runner-config"]["barcode_detector"])
            overlay_pipeline = None
            if "overlay" in self._piperun_config["runner-config"]:
                overlay_pipeline = channel.get_overlay_pipeline()
            channel.add_sink_element(output=self._piperun_config["outputs"][i],
                                     overlay_pipeline=overlay_pipeline,
                                     run_directory=self.run_directory)
            channel.add_fpscounter_element()
            channel.add_meta_element()

            channel.add_fakesink_element()

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

        command_with_args = ' '.join(standalone_args).replace(
            '(', '\(').replace(')', '\)').replace('"', '\\"')

        if "latency" in self._piperun_config["runner-config"]:
            latency_config = self._piperun_config["runner-config"]["latency"]
            latency_env = ""
            for k, v in latency_config.items():
                latency_env += "{}={} ".format(k, v)
            command_with_args = latency_env + command_with_args

        with open(command_path, "w") as command_file:
            command_file.write(command_with_args)
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
