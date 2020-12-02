'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import shlex
import subprocess
import urllib
import os
import json
from collections import namedtuple
from pipebench.schema.documents import rgetattr
from pipebench.tasks.frame_info import FrameInfo
import pipebench.tasks as tasks
from threading import Thread
import time
from pipebench.util import print_action
import sys

FRAME_INFO_MODULE = os.path.abspath(tasks.frame_info.__file__)

MediaType = namedtuple("MediaType", ["source","demux","parse",
                                     "encoded_caps",
                                     "frame_extension",
                                     "metapublish","sink"])

FpsReport = namedtuple("FpsReport",["fps","min","max","sample_avg","avg"])


MEDIA_TYPES = {
    "video/x-h264":MediaType("urisourcebin uri={}",
                             "qtdemux",
                             "h264parse",
                             "video/x-h264,alignment=au,stream-format=byte-stream",
                             "x-h264.bin",
                             None,
                             "multifilesink location={}/frame_%06d.x-h264.bin"),   
    "metadata/objects":MediaType(None,
                                 None,
                                 None,
                                 "metadata/objects,format=jsonl",
                                 None,
                                 "method=file file-format=json-lines file-path={}/objects.jsonl",
                                 "fakesink")              
}

INFERENCE_ELEMENTS = {
    "detect":"gvadetect",
    "classify":"gvaclassify",
    "inference":"gvainference",
    "track":"gvatrack",
    "audio-detect":"gvaaudiodetect"
}


def find_media(media, pipeline_root):
    extensions = [".mp4"]

    media_root = os.path.join(os.path.join(pipeline_root, "media"), media)

    file_paths = [
        file_path for file_path in os.listdir(media_root)
        if os.path.isfile(os.path.join(media_root, file_path)) and
        os.path.splitext(file_path)[1] in extensions
    ]

    media_base = os.path.basename(media)
    candidate_filenames = ["{}.{}".format(media_base, extension) for extension in extensions]
    for candidate_filename in candidate_filenames:
        if candidate_filename in file_paths:
            return os.path.join(media_root, candidate_filename)

    if len(file_paths) == 1:
        return os.path.join(media_root, file_paths[0])
    return None


def gst_launch(elements,vaapi=True):
    elements = " ! ".join(elements)
    command = "gst-launch-1.0 " + elements
    commandargs = shlex.split(command)
    print(' '.join(commandargs), flush=True)
    env = None
    print(os.getcwd())
    if not vaapi:
        env = dict(os.environ)
        if ("GST_VAAPI_ALL_DRIVERS" in env):            
            del env['GST_VAAPI_ALL_DRIVERS']
       
    result = subprocess.run(commandargs, env=env, check=False)
    return result.returncode == 0

def _create_inference_elements(models, inference_type, precision="FP32", properties={}):
    result = []
    
    model_list = getattr(models,inference_type,[])
    element = INFERENCE_ELEMENTS[inference_type]
    
    for model in model_list:
        model_element = []
        model_element.append("{} model={}".format(element,
                                                  rgetattr(model,"{}.xml".format(precision))))

        model_proc = rgetattr(model,"{}.proc".format(precision),None)

        if (not model_proc):
            model_proc = getattr(model,"proc",None)

        if (model_proc):
            model_element.append("model-proc={}".format(model_proc))

        for key,value in properties.items():
            model_element.append("{}={}",key,value)

        result.append(" ".join(model_element))
    return result


def create_reference(source_dir, target_dir, media_type, models, output_caps = None, timeout=60):

    caps_info = FrameInfo.read_caps(source_dir)
    caps = caps_info["caps"]
    original_media_source = caps_info["source"]
    source_media_type = MEDIA_TYPES[caps.split(',')[0]]
    source = "multifilesrc location={}/frame_%06d.{} caps=\"{}\"".format(source_dir,
                                                                         source_media_type.frame_extension,
                                                                         caps)

    decode = "decodebin sink-caps=\"{}\"".format(caps)

    
    detect = _create_inference_elements(models,"detect")

    classify = _create_inference_elements(models,"classify")

    output_media_type = MEDIA_TYPES[media_type]

    metapublish = None
    metaconvert = None
    if (output_media_type.metapublish):
        
        metaconvert = "gvametaconvert add-empty-results=true source=\"{}\"".format(original_media_source)
        metapublish = "gvametapublish " + output_media_type.metapublish.format(target_dir)



    frame_info = None
    if (not output_media_type.encoded_caps):
        frame_info = 'gvapython module={} class=FrameInfo arg=[\\\"{}\\\",\\\"{}\\\"]'.format(FRAME_INFO_MODULE,
                                                                                              target_dir,
                                                                                              source_dir)
    else:
        with open(os.path.join(target_dir,"caps.json"),"w") as caps_file:
            caps = {"caps":output_media_type.encoded_caps}
            json.dump(caps,caps_file)
    
        
    sink = "fakesink"
    if (output_media_type.sink.format(target_dir)):
        sink = output_media_type.sink.format(target_dir)

    timeout_element = None
    if (timeout):
        timeout_element='gvapython module={} class=Timeout arg=[{}]'.format(FRAME_INFO_MODULE,
                                                                            timeout)

    elements = [source,timeout_element,decode]
    elements.extend(detect)
    elements.extend(classify)
    elements.extend([metaconvert,metapublish,frame_info,sink])

    elements = [ element for element in elements if element ]       
        
    return gst_launch(elements,vaapi=False)


def read_caps(input_path):
    return FrameInfo.read_caps(input_path)

def create_encoded_frames(target_dir, media_type, media):

    if (media_type not in MEDIA_TYPES):
        raise Exception("Unsupported Media Type: {}".format(media_type))

    media_type = MEDIA_TYPES[media_type]
    media_uri = None

    if (os.path.isfile(media)):
        media_uri = urllib.parse.urlunsplit(["file",None,media,None,None])
    else:
        raise Exception("Media is not a file: {}".format(media))

    source = media_type.source.format(media_uri)
    demux = media_type.demux
    parse = media_type.parse
    encoded_caps = media_type.encoded_caps
    frame_info = 'gvapython module={} class=FrameInfo arg=[\\\"{}\\\",\\\"{}\\\"]'.format(FRAME_INFO_MODULE,target_dir,media_uri)
    sink = "multifilesink location={}/frame_%06d.{}".format(target_dir,media_type.frame_extension)
    return gst_launch([source,demux,parse,encoded_caps,frame_info,sink],vaapi=False)


class MediaSink(Thread):

    def _load_frame_sizes(self):
            
        frame__paths = [ os.path.join(self._reference_dir, path)
                         for path in os.listdir(self._reference_directory)
                         if path.endswith(self._media_type.frame_extension) ]

        frame_paths.sort(key= lambda item: int(item.split('_')[1].split('.')[0]))
        
        frame_sizes = [ os.path.getsize(path) for path in frame_paths if os.path.isfile(path) ]

        return frame_sizes
    
    def __init__(self,
                 source_path,
                 source_uri,
                 caps,
                 reference_directory = None,
                 warm_up = 0,
                 sample_size = 1,
                 *args,
                 **kwargs):

        self._reference_directory = reference_directory
        self._source_path = source_path
        self._warm_up = warm_up
        self._frame_count = 0
        self._start_time = None
        self._media_type = MEDIA_TYPES[caps.split(',')[0]]
        self._min_sample_fps =  sys.maxsize
        self._max_sample_fps = 0
        self._last_sample_fps = 0
        self._total_sample_fps = 0
        self._avg_fps = 0
        self._avg_sample_fps = 0
        self._sample_size = sample_size
        self._sample_count = 0
        self._source_uri = source_uri
        self.connected = False
        self._stopped = False
        
        if ("jsonl" in self._media_type.encoded_caps):
            self._frame_sizes = None
            self.run = self.read_lines
        else:
            self._frame_sizes = _load_frame_sizes()
            self.run = self.read_frames
        
        
        super().__init__(*args, **kwargs)

    def get_fps(self):
        return FpsReport(self._last_sample_fps,
                         self._min_sample_fps,
                         self._max_sample_fps,
                         self._avg_sample_fps,
                         self._avg_fps)

    def stop(self):
        self._stopped = True
        
    def read_lines(self):

        while(not self._stopped):

            print_action("Starting: pipebench memory sink",
                         ["Started: {}".format(time.time()),
                          "URI: {}".format(self._source_uri)])

            with open(self._source_path,"rb") as source_fifo:
                self.connected = True
                next_char = ""
                line = bytearray()
                while next_char != None:
                    line.clear()
                    next_char = ""
                    while(next_char != b'\n'):
                        next_char = source_fifo.read(1)
                        if (not next_char):
                            break
                        line.extend(next_char)
                    if (not next_char):
                        break
                    #print(json.loads(str(line,"utf-8")))
                    self._frame_count = self._frame_count + 1

                    if (self._frame_count % self._sample_size == 0):
                        self._sample_count += 1
                        if (self._sample_count >= self._warm_up):
                            current_time = time.time()
                            if (not self._start_time):
                                self._start_time = current_time
                                self._last_start_time = current_time
                                self._start_frame_count = self._frame_count
                                continue
                            self._last_sample_fps = self._sample_size / (current_time - self._last_start_time)
                            if (self._last_sample_fps > self._max_sample_fps):
                                self._max_sample_fps = self._last_sample_fps
                            if (self._last_sample_fps < self._min_sample_fps):
                                self._min_sample_fps = self._last_sample_fps
                            self._total_sample_fps += self._last_sample_fps
                            self._avg_sample_fps = self._total_sample_fps / (self._sample_count-self._warm_up)
                            self._last_start_time = current_time
                            self._avg_fps = (self._frame_count - self._start_frame_count) / (current_time - self._start_time)

            self.connected = False
            print_action("Ended: pipebench memory sink",
                         ["Ended: {}".format(time.time()),
                          "Frames Read: {}".format(self._frame_count)])



    def read_frames(self):
        pass


class MediaSource(Thread):

    def _read_file(self,path):
        with open(path,"rb") as input:
            return input.read()

    def _read_input(self):

        frame_paths = [ os.path.join(self._input_directory, path)
                         for path in os.listdir(self._input_directory)
                         if path.endswith(self._media_type.frame_extension) ]
             
        frame_paths = [ frame_path for frame_path in frame_paths if os.path.isfile(frame_path) ]
        
        frame_paths.sort(key= lambda item: int(os.path.basename(item).split('_')[1].split('.')[0]))

        return [self._read_file(frame_path) for frame_path in frame_paths]

    
    def __init__(self,
                 sink_path,
                 sink_uri,
                 caps,
                 input_directory,
                 frame_rate=-1,
                 frame_count = -1,
                 elapsed_time=-1,
                 *args, **kwargs):

        self._media_type = MEDIA_TYPES[caps.split(',')[0]]
        self._sink_path = sink_path
        self._sink_uri = sink_uri
        self._input_directory = input_directory
        self._frames = self._read_input()
        self._frame_rate = frame_rate
        self._frame_count = frame_count
        self.connected = False
        self._stopped = False

        if (self._frame_count == -1) and (elapsed_time != -1 ) and (self._frame_rate>-1):
            self._frame_count = elapsed_time * self._frame_rate

        self._sleep_time = 0

        if (self._frame_rate != -1 ):
            self._sleep_time = 1 / (self._frame_rate + 0.5)
            
        super().__init__(*args, **kwargs)

        if (not self._frames):
            raise Exception("No input found please regenerate using --force")

    def stop(self):
        self._stopped = True
    
    def run(self):
        
        while(not self._stopped):
        
            start_time = time.time()
            count = 0
            frame_len = len(self._frames)


            print_action("Starting: pipebench memory source",
                         ["Started: {}".format(start_time),
                          "URI: {}".format(self._sink_uri)])
            self.connected = False
            with open(self._sink_path,"wb", buffering=0) as sink_fifo:
                self.connected = True
                try:
                    while(not self._stopped):
                        written = sink_fifo.write(self._frames[count % frame_len])
                        time.sleep(self._sleep_time)
                        count += 1
                        if (self._frame_count!=-1) and (count>=self._frame_count):
                            self._stopped = True
                       
                except BrokenPipeError as error:
                    print_action("Ended: pipebench memory source",
                                 ["Ended: {}".format(time.time()),
                                  "Frames Written: {}".format(count+1)])

                    continue

            break

        self.connected = False
        
        print_action("Ended: pipebench memory source",
                     ["Ended: {}".format(time.time()),
                      "Frames Written: {}".format(count+1)])
        


        
