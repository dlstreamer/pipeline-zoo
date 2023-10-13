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

class ObjectDetection(Task):
    names = ["object-detection"]
    OUTPUT_CAPS = "metadata/objects,format=jsonl"
    
    def __init__(self, pipeline, task, measurement_settings, args):
        super().__init__(pipeline, task, measurement_settings, args)
        self._output_media_type = "metadata/objects"

        self._use_reference_detections = measurement_settings.get(
            "use-reference-detections",
            False)
       
        if (self._task_name != "object-classification"
            and self._use_reference_detections):
            args.parser.error("use reference detections only valid for classification pipelines")

    def _prepare_output_caps(self):
        self._output_caps.append(ObjectDetection.OUTPUT_CAPS)
        
    def _create_piperun_config(self, run_root, runner_config, number_of_streams=1):

        if self._use_reference_detections:
            self._pipeline._document["detection-model"] = (
                os.path.join(self._args.workload_root,
                             "reference",
                             "detection.objects.jsonl")
                )
        return super()._create_piperun_config(run_root, runner_config, number_of_streams)

    def _get_models(self):
        models = SimpleNamespace()

        detection_model = self._pipeline._document.get("detection-model",None)

        if not detection_model:
            detection_model = self._pipeline._document.get("model",None)
                
        detection_model = find_model(detection_model,
                                     self._pipeline.pipeline_root,
                                     self._args)
        
        models.detect = [detection_model]
        models.classify = []

        classification_models = self._pipeline._document.get("classification-models",[])
        
        for classification_model in classification_models:
            if isinstance(classification_model,list):
                raise Exception("Dependent classification not supported!")
            models.classify.append(find_model(classification_model,
                                              self._pipeline.pipeline_root,
                                              self._args))
        return models
            
