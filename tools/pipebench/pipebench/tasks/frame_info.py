'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import os
import json
import time

class Timeout:
    def __init__(self, duration = 60):
        self._duration = duration
        self._start = None
    def process_frame(self, frame):
        if (not self._start):
            self._start = time.time()
        elif ((time.time()-self._start) >self._duration):
            return False
        return True

                
class FrameInfo:

    def __init__(self, output_path, source):
        self._output_path = output_path
        self._initialized = False
        self._source = source

    def write_caps(self, frame):
        path = "{}/caps.json".format(self._output_path)
        try:
            os.makedirs(self._output_path,exist_ok=True)
            os.remove(path)
        except Exception as e:
            pass
        
        with open(path,"w") as file:
            value = {'caps':str(frame.caps),
                     'source':self._source}
            file.write(json.dumps(value))
            file.flush()

    @staticmethod
    def read_caps(input_path):
        path = "{}/caps.json".format(input_path)
        caps = None
        with open(path,"r") as file:
            caps = json.load(file)
            
        return caps
        
    
    def process_frame(self,frame):
        if (not self._initialized):
            self.write_caps(frame)
            self._initialized = True
        return True
