from tasks.task import Task
from tasks.object_detection import ObjectDetection

class ObjectClassification(ObjectDetection, Task):
    supported_tasks = ["object-classification"]

    detect_model_config = "detection-model"

    classify_model_config = "classification-models"

    def __init__(self, piperun_config, args, *pos_args, **keywd_args):
        super().__init__(piperun_config, args, *pos_args, **keywd_args)
