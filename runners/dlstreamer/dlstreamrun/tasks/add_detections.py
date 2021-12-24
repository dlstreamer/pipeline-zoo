'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import json
import time
                
class AddDetections:

    def _load_reference(self, reference_path):
    
        reference = []

        try:
            with open(reference_path,"r") as reference_file:
                for result in reference_file:
                    try:
                        reference.append(json.loads(result))
                    except Exception as error:
                        if (result == "\n"):
                            continue
                        else:
                            raise
        except Exception as error:
            print("Can't load reference! {}".format(error))
            
        return reference

    
    def __init__(self, reference_path):
        self._reference = self._load_reference(reference_path)
        self._frame_count = 0
        self._reference_length = len(self._reference)
        
    
    def process_frame(self,frame):
        result = self._reference[self._frame_count % self._reference_length]
        objects = result.get("objects",[])
        for object_ in objects:
            detection = object_.get("detection",None)
            confidence = detection.get("confidence",0.0)
            label_id = detection.get("label_id",None)
            if detection:
                label = object_.get("label","")
                region = frame.add_region(object_["x"],
                                          object_["y"],
                                          object_["w"],
                                          object_["h"],
                                          label,
                                          confidence)
                if label_id:
                    region.detection()["label_id"] = label_id
                                 
        self._frame_count += 1
        return True
