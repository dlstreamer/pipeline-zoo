from tasks.task import Task
import copy
from tasks.object_detection import ObjectDetection

class ObjectDetectionMulti(ObjectDetection, Task):
    supported_tasks = ["object-detection-multi"]

    detect_model_config = "detection-model"

    classify_model_config = "classification-models"
    
    multi_detect_model_config = "multi-detection-models"

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        if self.multi_detect_model_config not in piperun_config["pipeline"]:
            self.multi_detect_model_config = None
        super().__init__(piperun_config, args, *pos_args, **keywd_args)
        classify_model_config = self._piperun_config["pipeline"][self.classify_model_config]
        
        if self.multi_detect_model_config:
            multi_detect_model_config = self._piperun_config["pipeline"][self.multi_detect_model_config]

        for i in range(len(self._piperun_config["inputs"])):
            self._channels[i].add_classify_element(copy.deepcopy(classify_model_config))
            if self.multi_detect_model_config:
                self._channels[i].add_multi_detect_element(copy.deepcopy(multi_detect_model_config))

        self.create_command()