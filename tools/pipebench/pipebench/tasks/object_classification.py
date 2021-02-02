'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''
from pipebench.tasks.task import Task
from pipebench.tasks.object_detection import ObjectDetection

class ObjectClassification(ObjectDetection, Task):
        names = ["object-classification"]

        def __init__(self, piperun, task, workload, args):
            super().__init__(piperun, task, workload, args)

