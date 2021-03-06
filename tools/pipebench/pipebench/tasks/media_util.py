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
from threading import Lock
import time
from pipebench.util import print_action
import sys
import ffmpeg
import math
import tempfile

FRAME_INFO_MODULE = os.path.abspath(tasks.frame_info.__file__)

MediaType = namedtuple("MediaType", ["source",
                                     "demux",
                                     "parse",
                                     "encoded_caps",
                                     "frame_extension",
                                     "metapublish",
                                     "sink",
                                     "container_formats",
                                     "elementary_stream_extensions"])

FpsReport = namedtuple("FpsReport",["fps","min","max","sample_avg","avg","start","end"])


MEDIA_TYPES = {
    "video/x-h264":MediaType("urisourcebin uri={}",
                             "qtdemux",
                             "h264parse",
                             "video/x-h264,alignment=au,stream-format=byte-stream",
                             "x-h264.bin",
                             None,
                             "multifilesink location={}/frame_%06d.x-h264.bin",
                             ["mp4"],
                             ["h264","264"]),
    "video/x-h265":MediaType("urisourcebin uri={}",
                             "qtdemux",
                             "h265parse",
                             "video/x-h265,alignment=au,stream-format=byte-stream",
                             "x-h265.bin",
                             None,
                             "multifilesink location={}/frame_%06d.x-h265.bin",
                             ["mp4"],
                             ["h265","265"]),   
    "metadata/objects":MediaType(None,
                                 None,
                                 None,
                                 "metadata/objects,format=jsonl",
                                 None,
                                 "method=file file-format=json-lines file-path={}/objects.jsonl",
                                 "fakesink",
                                 [],
                                 []),
    "metadata/line-per-frame":MediaType(None,
                                        None,
                                        None,
                                        "metadata/objects,format=jsonl",
                                        None,
                                        "method=file file-format=json-lines file-path={}/objects.jsonl",
                                        "fakesink",
                                        [],
                                        []),
    "video/x-raw":MediaType("urisourcebin uri={}",
                            "decodebin ! videoconvert",
                            None,
                            None,
                            "raw.bin",
                            None,
                            "multifilesink location={}/frame_%06d.raw.bin",
                            ["mp4"],
                            ["raw.bin"])             
}

INFERENCE_ELEMENTS = {
    "detect":"gvadetect",
    "classify":"gvaclassify",
    "inference":"gvainference",
    "track":"gvatrack",
    "audio-detect":"gvaaudiodetect"
}

def _get_media_extensions(media_type_keys = None):
    result = set()
    for media_type_key, media_type in MEDIA_TYPES.items():
        if media_type_keys and media_type_key not in media_type_keys:
            continue
        if (media_type.frame_extension):
            result.add(media_type.frame_extension)
        for container_format in media_type.container_formats:
            result.add(container_format)
        for extension in media_type.elementary_stream_extensions:
            result.add(extension)
    return result

def find_media(media, pipeline_root, media_type_keys = None):
    extensions = [ ".{}".format(extension) for extension in _get_media_extensions(media_type_keys) ]
    media_root = os.path.join(os.path.join(pipeline_root, "media"), media)
    if os.path.isdir(media_root):
        file_paths = [
            file_path for file_path in os.listdir(media_root)
            if os.path.isfile(os.path.join(media_root, file_path)) and
            os.path.splitext(file_path)[1] in extensions
        ]
        media_base = os.path.basename(media)
        candidate_filenames = ["{}{}".format(media_base, extension) for extension in extensions]
        for candidate_filename in candidate_filenames:
            if candidate_filename in file_paths:
                return os.path.join(media_root, candidate_filename)   
        if len(file_paths) == 1:
            return os.path.join(media_root, file_paths[0])
    elif os.path.isfile(media_root) and os.path.splitext(media_root)[1] in extensions:
        return media_root
    else:
        return None
    return None


def gst_launch(elements,vaapi=True):
    elements = " ! ".join([element for element in elements if element])
    command = "gst-launch-1.0 --no-fault " + elements
    commandargs = shlex.split(command)
    env = None
    if not vaapi:
        env = dict(os.environ)
        if ("GST_VAAPI_ALL_DRIVERS" in env):            
            del env['GST_VAAPI_ALL_DRIVERS']
        feature_rank = "vaapidecodebin:NONE"
        if ("GST_PLUGIN_FEATURE_RANK" in env):
            feature_rank = "{},{}".format(env["GST_PLUGIN_FEATURE_RANK"], feature_rank)
        env["GST_PLUGIN_FEATURE_RANK"] = feature_rank
    result = subprocess.run(commandargs,
                            env=env,
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    return result.returncode == 0

def _create_inference_elements(models, inference_type, precision="FP32", properties={}):
    result = []
    
    model_list = getattr(models,inference_type,[])
    element = INFERENCE_ELEMENTS[inference_type]

    for model in model_list:

        if isinstance(model,str) and (model == 'full_frame'):
            result.append(model)
            continue
        
        model_element = []        
        if (not hasattr(model, precision)):
            default_precision = list(model.__dict__.keys())[0]
            print("\nNo {} Model found, trying: {}\n".format(precision, default_precision))
            precision = default_precision
        
        model_element.append("{} model={}".format(element,
                                                  rgetattr(model,"{}.xml".format(precision))))

        model_proc = rgetattr(model,"{}.proc".format(precision),None)

        if (not model_proc):
            model_proc = getattr(model,"proc",None)

        if (model_proc):
            model_element.append("model-proc={}".format(model_proc))

        for key,value in properties.items():
            model_element.append("{}={}".format(key,value))

        result.append(" ".join(model_element))
    return result


def create_reference(source_dir,
                     target_dir,
                     media_type,
                     models,
                     region = None,
                     resolution = None,
                     color_space = None,
                     output_caps=None,
                     timeout=60,
                     individual_frames=True):

    caps_info = FrameInfo.read_caps(source_dir)
    caps = caps_info["caps"]
    original_media_source = caps_info["source"]
    source_media_type = MEDIA_TYPES[caps.split(',')[0]]
    if (individual_frames):
        source = "multifilesrc location={}/frame_%06d.{} caps=\"{}\"".format(source_dir,
                                                                             source_media_type.frame_extension,
        caps)
    else:
        source = "filesrc location={}/stream.{} ! \"{}\"".format(source_dir,
                                                                 source_media_type.elementary_stream_extensions[0],
                                                                 caps)

    if "PIPELINE_ZOO_PLATFORM" in os.environ and os.environ["PIPELINE_ZOO_PLATFORM"]=="VCAC_A":
        decode = "avdec_h264 "
    elif individual_frames:
        decode = "decodebin sink-caps=\"{}\"".format(caps)
    else:
        decode = "decodebin"

    crop = None

    csc = None
    if color_space:
        csc = "videoconvert"

    scale = None
    if resolution:
        scale = "videoscale"

    detect = _create_inference_elements(models, "detect")
    properties = {}
    if detect and detect[0]=="full_frame":
        properties['inference-region']="full-frame"
        detect = []
    classify = _create_inference_elements(models,"classify",properties=properties)

    output_media_type = MEDIA_TYPES[media_type.split(',')[0]]
    metapublish = None
    metaconvert = None
    capsfilter = None
    
    if (output_media_type.metapublish):        
        metaconvert = "gvametaconvert add-empty-results=true source=\"{}\"".format(original_media_source)
        metapublish = "gvametapublish " + output_media_type.metapublish.format(target_dir)
    else:
        capsfilter = media_type

    frame_info = None
    if (not output_media_type.encoded_caps):
        frame_info = 'gvapython module={} class=FrameInfo arg=[\\\"{}\\\",\\\"{}\\\"]'.format(FRAME_INFO_MODULE,
                                                                                              target_dir,
                                                                                              source_dir)
    else:
        with open(os.path.join(target_dir,"caps.json"),"w") as caps_file:
            caps = {"caps":output_media_type.encoded_caps}
            json.dump(caps, caps_file)
            
    sink = "fakesink"
    if (output_media_type.sink.format(target_dir)):
        sink = output_media_type.sink.format(target_dir)

    timeout_element = None
    if (timeout and individual_frames):
        timeout_element='gvapython module={} class=Timeout arg=[{}]'.format(FRAME_INFO_MODULE,
                                                                            timeout)

    elements = [source, timeout_element, decode, crop, scale, csc]
    elements.extend(detect)
    elements.extend(classify)
    elements.extend([metaconvert, metapublish, capsfilter, frame_info, sink])

    elements = [ element for element in elements if element ]       
        
    return gst_launch(elements, vaapi=False)


def read_caps(input_path):
    return FrameInfo.read_caps(input_path)

def _stream_info(input_media):
    probe_info = ffmpeg.probe(input_media,count_packets=None)['streams'][0]
    frame_rate = probe_info["r_frame_rate"].split('/')
    frame_rate = float(int(frame_rate[0])/int(frame_rate[1]))
    return int(probe_info["nb_read_packets"]), frame_rate

def _convert_frame_rate(input_media,
                        media_type,
                        target_fps,
                        target_dir):
    temp_output_path = os.path.join(target_dir,
                               "stream.fps.temp.{}".format(
                                   media_type.elementary_stream_extensions[0]))

    command_args = ["ffmpeg",
                    "-nostdin",
                    "-y",
                    "-i",
                    input_media,
                    "-c","copy",
                    temp_output_path]
    
    
    result = subprocess.run(command_args,
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)

    if result.returncode != 0:
        return None

    output_path = os.path.join(target_dir,
                               "stream.fps.{}".format(
                                   media_type.container_formats[0]))

    command_args = ["ffmpeg",
                    "-nostdin",
                    "-y",
                    "-r","{}".format(target_fps),
                    "-i",
                    temp_output_path,
                    "-c", "copy",
                    output_path]

    result = subprocess.run(command_args,
                            check=False,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)

    if result.returncode == 0:
        return output_path
    else:
        return None
    
def _concat_stream(input_media, frame_count, target_frame_count, target_dir):
    number_of_copies = math.ceil(target_frame_count/frame_count)
    extension = os.path.splitext(input_media)[1]
    output_path = os.path.join(target_dir,
                               "stream.concat{}".format(extension))
    with tempfile.TemporaryDirectory() as temp_directory:
        concat_path = "{}/concat.txt".format(temp_directory)
        with open(concat_path,
                  "w") as concat_file:
            for _ in range(number_of_copies):
                concat_file.write("file '{}'\n".format(input_media))
        
        command_args = ["ffmpeg",
                        "-nostdin",
                        "-y",
                        "-safe","0",
                        "-f", "concat",
                        "-i", concat_path,
                        "-c","copy",
                        output_path]


        result = subprocess.run(command_args,
                                check=False,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
    if result.returncode==0:
        return output_path
    else:
        return None

def create_encoded_stream(target_dir, media_type, media,
                          individual_frames=True,
                          duration=60,
                          target_fps=30):

    if (media_type not in MEDIA_TYPES):
        raise Exception("Unsupported Media Type: {}".format(media_type))

    media_type = MEDIA_TYPES[media_type]
    media_uri = None
    if (os.path.isfile(media)):

        frame_count, frame_rate = _stream_info(media)

        if target_fps == 0:
            target_fps = frame_rate

        if duration == 0:
            duration = frame_count / target_fps
        else:
            target_frame_count = (duration * target_fps * 2)
            if frame_count < target_frame_count:
                media = _concat_stream(media,
                                       frame_count,
                                       target_frame_count,
                                       target_dir)
            
        if frame_rate != target_fps:
            media = _convert_frame_rate(media,
                                        media_type,
                                        target_fps,
                                        target_dir)
        media_uri = urllib.parse.urlunsplit(["file",None,media,None,None])
    else:
        raise Exception("Media is not a file: {}".format(media))

    source = media_type.source.format(media_uri)
    extension = os.path.splitext(media)[1]
    if (extension[1:] in media_type.container_formats):
        demux = media_type.demux
    else:
        demux = None
    parse = media_type.parse
    encoded_caps = media_type.encoded_caps
    frame_info = 'gvapython module={} class=FrameInfo arg=[\\\"{}\\\",\\\"{}\\\"]'.format(FRAME_INFO_MODULE,target_dir,media_uri)
    if individual_frames:
        sink = "multifilesink location={}/frame_%06d.{}".format(target_dir,
                                                                media_type.frame_extension)
    else:
        sink = "filesink location={}/stream.{}".format(target_dir,media_type.elementary_stream_extensions[0])

    return gst_launch([source,demux,parse,encoded_caps,frame_info,sink],vaapi=False), duration, target_fps



class MediaSink(Thread):

    def _load_frame_sizes(self):
        frame_paths = [ os.path.join(self._reference_directory, path)
                         for path in os.listdir(self._reference_directory)
                         if path.endswith(self._media_type.frame_extension) ]
        frame_paths.sort(key= lambda item: int(item.split('_')[-1].split('.')[0]))
        
        frame_sizes = [ os.path.getsize(path) for path in frame_paths if os.path.isfile(path) ]

        return frame_sizes
    
    def __init__(self,
                 source_path,
                 source_uri,
                 caps,
                 stream_index = 0,
                 reference_directory = None,
                 warm_up = 0,
                 sample_size = 1,
                 save_pipeline_output = False,
                 output_dir = None,
                 semaphore = None,
                 verbose_level = 0,
                 *args,
                 **kwargs):
        self._semaphore = semaphore
        self._reference_directory = reference_directory
        self._source_path = source_path
        self._warm_up = warm_up
        self._frame_count = 0
        self._start_time = None
        self._end_time = None
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
        self._save_pipeline_output = save_pipeline_output
        self._output_file = None
        self._output_dir = output_dir
        self._stream_index = stream_index
        self._verbose_level = verbose_level
        if (self._media_type.encoded_caps) and ("jsonl" in self._media_type.encoded_caps):
            self._frame_sizes = None
            self.run = self.read_lines
            if self._save_pipeline_output:
                self._output_file = open(os.path.join(output_dir,
                                                      "stream_{}.objects.jsonl".format(stream_index)),
                                         "wb")
        else:
            self._frame_sizes = self._load_frame_sizes()
            self.run = self.read_frames
        
        
        super().__init__(*args, **kwargs)

    def get_fps(self):
        return FpsReport(self._last_sample_fps,
                         self._min_sample_fps,
                         self._max_sample_fps,
                         self._avg_sample_fps,
                         self._avg_fps,
                         self._start_time,
                         self._end_time)

    def stop(self):
        self._stopped = True
        
    def read_lines(self):

        while(not self._stopped):

            if (self._semaphore):
                self._semaphore.acquire()
            if self._verbose_level > 2:
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
                        next_char = None if self._stopped else source_fifo.read(1)
                        if (not next_char):
                            self._end_time = time.time()
                            break
                        line.extend(next_char)
                    if (not next_char):
                        break
                    if self._save_pipeline_output:
                        self._output_file.write(line)
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
            if not self._end_time:
                self._end_time = time.time()
            if self._verbose_level > 2:
                print_action("Ended: pipebench memory sink",
                             ["Ended: {}".format(time.time()),
                              "URI: {}".format(self._source_uri),
                              "Frames Read: {}".format(self._frame_count)])
            if self._output_file:
                self._output_file.close()



    def read_frames(self):
        input_len = len(self._frame_sizes)

        while(not self._stopped):

            if (self._semaphore):
                self._semaphore.acquire()

            print_action("Starting: pipebench memory sink",
                         ["Started: {}".format(time.time()),
                          "URI: {}".format(self._source_uri)])


            with open(self._source_path,"rb") as source_fifo:
                self.connected = True
                bytes_read = 1
                frame = bytearray()
                # read input frame
                while(bytes_read):
                    bytes_read = 0
                    frame_size = self._frame_sizes[self._frame_count %input_len]
                    frame.clear()
                    while(bytes_read<frame_size):
                        if self._stopped:
                            bytes_read = 0
                        else:
                            bytes_ = source_fifo.read(frame_size-bytes_read)
                            frame.extend(bytes_)
                            bytes_read = bytes_read + len(bytes_)
                        if (not bytes_read):
                            self._end_time = time.time()
                            break

                    if (bytes_read):

                        self._frame_count += 1

                        if self._save_pipeline_output:
                            with open(os.path.join(self._output_dir,
                                                   "stream_{}.frame_{:06d}.raw.bin".format(self._stream_index,
                                                                                           self._frame_count)),
                                      "wb") as output:
                                output.write(frame)

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
            if not self._end_time:
                self._end_time = time.time()
            print_action("Ended: pipebench memory sink",
                         ["Ended: {}".format(time.time()),
                          "URI: {}".format(self._source_uri),
                          "Frames Read: {}".format(self._frame_count)])
            if self._output_file:
                self._output_file.close()   
        


class MediaSource(Thread):

    _frame_cache = {}
    _frame_cache_lock = Lock()

    def _read_file(self,path):
        with open(path,"rb") as input:
            return input.read()

    def _read_input(self):

        cache_key = (self._input_directory,self._media_type.frame_extension)

        frames = None

        with MediaSource._frame_cache_lock:
        
            frames = MediaSource._frame_cache.get(cache_key, None)

            if not frames:
                
                frame_paths = [ os.path.join(self._input_directory, path)
                                for path in os.listdir(self._input_directory)
                                if path.endswith(self._media_type.frame_extension) ]
            
                frame_paths = [ frame_path for frame_path in frame_paths if os.path.isfile(frame_path) ]
                
                frame_paths.sort(key= lambda item: int(os.path.basename(item).split('_')[1].split('.')[0]))

                MediaSource._frame_cache[cache_key] = [self._read_file(frame_path) for frame_path in frame_paths]
                
                frames = MediaSource._frame_cache[cache_key]
        
        return frames

    
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
        


        
