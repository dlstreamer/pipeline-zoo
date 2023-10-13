'''
* Copyright (C) 2023 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
from pipebench.tasks.task import Task
from pipebench.tasks.object_detection import ObjectDetection

class ObjectDetectionMulti(ObjectDetection, Task):
        names = ["object-detection-multi"]

        def __init__(self, piperun, task, workload, args):
            super().__init__(piperun, task, workload, args)

