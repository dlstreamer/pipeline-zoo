from tasks.task import Task
import copy
from tasks.object_detection import ObjectDetection

class ObjectTracking(ObjectDetection, Task):
    supported_tasks = ["object-tracking"]

    detect_model_config = "detection-model"

    inference_model_config = "inference-models"

    track_object_class = "track-object-class"

    classify_model_config = "classification-models"

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        if self.classify_model_config not in piperun_config["pipeline"]:
            self.classify_model_config = None
        
        super().__init__(piperun_config, args, *pos_args, **keywd_args)

        print("_piperun_config: {}".format(self._piperun_config))

        inference_model_config = self._piperun_config["pipeline"][self.inference_model_config]
        track_object_class_config = self._piperun_config["pipeline"][self.track_object_class]

        if self.classify_model_config:
            classify_model_config = self._piperun_config["pipeline"][self.classify_model_config]

        for i in range(len(self._piperun_config["inputs"])):
            self._channels[i].add_inference_element(copy.deepcopy(inference_model_config))
            self._channels[i].add_track_element(copy.deepcopy(track_object_class_config))
            if self.classify_model_config:
                self._channels[i].add_classify_element(copy.deepcopy(classify_model_config))

        self.create_command() 
