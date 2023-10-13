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
from pipebench.tasks.media_util import create_encoded_stream
import pipebench.tasks.media_util as media_util
from pipebench.tasks.media_util import create_reference
from pipebench.tasks.media_util import find_media
from pipebench.tasks.media_util import read_caps
from pipebench.tasks.media_util import MEDIA_TYPES
from pipebench.tasks.media_util import MediaSink
from pipebench.tasks.media_util import MediaSource
from .task import find_model
from types import SimpleNamespace
import yaml
import time
import uuid
from pipebench.tasks.runner_util import start_pipeline_runner
from threading import Thread
import time
import json
import tempfile

class DecodeVPP(Task):
    names = ["decode-vpp"]
    OUTPUT_CAPS = "video/x-raw"
    
    def __init__(self, pipeline, task, measurement_settings, args):
        super().__init__(pipeline, task, measurement_settings, args)
        self._output_media_type = "video/x-raw"      

    def _prepare_output_caps(self):
        if self._measurement_settings["save-pipeline-output"]:
                self._output_caps.append(DecodeVPP.OUTPUT_CAPS)
                if "color-space" in self._pipeline._document:
                    self._output_caps[-1] += ",format={}".format(self._pipeline._document["color-space"].upper())

                if "resolution" in self._pipeline._document:
                    self._output_caps[-1] += ",height={},width={}".format(self._pipeline._document["resolution"]["height"],
                                                                          self._pipeline._document["resolution"]["width"])

        else:
            self._output_caps.append("metadata/line-per-frame,format=jsonl")