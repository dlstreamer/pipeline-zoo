'''
* Copyright (C) 2019-2020 Intel Corporation.
*
* SPDX-License-Identifier: BSD-3-Clause
'''

import abc
import uuid
import yaml
import json
import jsonschema
from jsonschema import Draft7Validator, validators, RefResolver
from types import SimpleNamespace
from pipebench.schema.documents import PipelineConfig
from pipebench.tasks.media_util import create_encoded_stream
from pipebench.tasks.media_util import create_reference
from pipebench.tasks.media_util import find_media
from pipebench.tasks.media_util import read_caps
from pipebench.tasks.media_util import MEDIA_TYPES
from pipebench.tasks.media_util import MediaSink
from pipebench.tasks.media_util import MediaSource
from pipebench.util import create_directory
from pipebench.tasks.runner_util import start_pipeline_runner
import os
from pipebench.schema.documents import rsetattr
import tempfile

def _set_namespace_value(namespace,path,value):
    current = namespace
    for segment in path[:-1]:
        if segment not in vars(current):
            setattr(current,segment,SimpleNamespace())

        current = getattr(current,segment)

    setattr(current,path[-1],value)


def _split_path(path):

    segments = []
    
    while 1:
        prefix, suffix = os.path.split(path)
        if prefix == path:  # sentinel for absolute paths
            segments.insert(0, prefix)
            break
        elif suffix == path: # sentinel for relative paths
            segments.insert(0, suffix)
            break
        else:
            path = prefix
            segments.insert(0, suffix)
            
    return segments

def set_model_file(model, model_root, file_paths, root, result, extension, key):
    candidates = [file_path for file_path in file_paths if file_path.endswith(extension)]
    
    candidate = "{}{}".format(model,extension)
    
    value = None
        
    if (candidate in candidates):
        value = os.path.join(root,candidate)
    elif (len(candidates)==1):
        value = os.path.join(root,candidates[0])

    if (value):
        rel_path = os.path.relpath(value,model_root)
        
        segments = _split_path(rel_path)[:-1]
        
        segments.append(key)
        
        _set_namespace_value(result, segments, value)


def find_model(model, pipeline_root, args):

    if model == "full_frame":
        return model

    result = SimpleNamespace()
        
    model_root = os.path.join(os.path.join(pipeline_root, "models"), model)

    if (not os.path.isdir(model_root)):
        raise Exception("Can't find model root for: {}".format(model))

    for root, directories, file_paths in os.walk(model_root):

        set_model_file(model, model_root, file_paths, root, result, ".json", "proc")

        set_model_file(model, model_root, file_paths, root, result, ".xml", "xml")

        set_model_file(model, model_root, file_paths, root, result, ".bin", "bin")
            
    return result

def find_pipeline(pipeline, args):
    pipelines_root = args.workspace_root
    pipeline_root = None
    
    for root, directories, files in os.walk(pipelines_root):
        if (pipeline in directories):
            pipeline_root = os.path.abspath(os.path.join(root,pipeline))
            break

    if (not pipeline_root):
        if (os.path.isdir(pipeline)):
            pipeline_root = os.path.abspath(pipeline)

    if (not pipeline_root):
        return None

    file_paths = [ file_path for file_path in os.listdir(pipeline_root)
                   if os.path.isfile(os.path.join(pipeline_root,file_path)) and
                   file_path.endswith(".pipeline.yml")] 

    candidate_filename = "{}.pipeline.yml".format(pipeline)

    if candidate_filename in file_paths:
        return os.path.join(pipeline_root,candidate_filename)

    if len(file_paths)==1:
        return os.path.join(pipeline_root,file_paths[0])
    
    return None


class Task(object, metaclass=abc.ABCMeta):

    task_map = None
    
    @property
    @classmethod
    @abc.abstractmethod
    def names(cls):
        pass

    def __init__(self, pipeline, task, measurement_settings, args):
        self._measurement_settings = measurement_settings
        self._task = task
        self._pipeline = pipeline
        self._args = args
        self._fps_stats = None
        self._task_name = self._pipeline._namespace.task
        self._output_media_type = ""

    def _prepare_output_caps(self):
        pass

    def _create_piperun_config(self, run_root, runner_config, number_of_streams=1):
        piperun_config = {"pipeline":self._pipeline._document}       
        filename = "{}.piperun.yml".format(self._args.measurement)

        self._output_caps = []
        self._output_paths = []
        self._output_uris = []
        self._input_caps = []
        self._input_paths = []
        self._input_uris = []
        inputs = []
        outputs = []
        tmpdir = tempfile.mkdtemp()

        for i in range(number_of_streams):
            pipe_uuid = uuid.uuid1()
            pipe_directory = os.path.join(tmpdir,str(pipe_uuid))
            create_directory(pipe_directory)
            if (self._measurement_settings["scenario"]["source"]=="memory"):
                self._input_caps.append(read_caps(os.path.join(self._args.workload_root,"input"))["caps"])
                self._input_paths.append( "{}/input".format(pipe_directory))
                self._input_uris.append( "pipe://{}".format(self._input_paths[-1]))
            elif (self._measurement_settings["scenario"]["source"]=="disk"):
                self._input_caps.append(read_caps(os.path.join(self._args.workload_root,"input"))["caps"].split(',')[0])
                media_type = MEDIA_TYPES[self._input_caps[-1]]


                media_file = os.path.join(self._args.workload_root,
                                          "input",
                                           "stream.{}".format(media_type.elementary_stream_extensions[0]))

                fps_candidate = os.path.join(self._args.workload_root,
                                         "input",
                                         "stream.fps.{}".format(media_type.container_formats[0]))
                if os.path.isfile(fps_candidate):
                    media_file = fps_candidate
                
                self._input_paths.append(media_file)
                
                self._input_uris.append("file://{}".format(self._input_paths[-1]))

            media_type_key = read_caps(os.path.join(self._args.workload_root,"input"))["caps"].split(',')[0]
            inputs.append( {"uri":self._input_uris[-1],
                            "caps":self._input_caps[-1],
                            "extended-caps":read_caps(os.path.join(self._args.workload_root,"input"))["caps"],
                            "source":find_media(self._measurement_settings["media"],self._pipeline.pipeline_root,media_type_keys=[media_type_key])})
            
            self._prepare_output_caps()
            self._output_paths.append("{}/output".format(pipe_directory))
            self._output_uris.append("pipe://{}".format(self._output_paths[-1]))
            outputs.append({"uri":self._output_uris[-1],
                            "caps":self._output_caps[-1]})

            piperun_config["inputs"] = inputs
            piperun_config["outputs"] = outputs
            piperun_config["runner-config"] = runner_config
            piperun_config["models-root"] = os.path.join(self._pipeline.pipeline_root,"models")
            piperun_config["pipeline-root"] = self._pipeline.pipeline_root
            piperun_config_path = os.path.join(run_root,filename)

        if (self._args.runner == "mockrun"):
            runner_config["workload-root"] = self._args.workload_root

        if (not self._args.force) and (os.path.isfile(piperun_config_path)):
            return
    
        with open(piperun_config_path,"w") as piperun_config_file:
            yaml.dump(piperun_config,
                    piperun_config_file,
                    sort_keys=False,
                    version=(1,0))
            
        return piperun_config_path

        
    def run(self,
            run_root,
            runner_config,
            warm_up,
            frame_rate,
            sample_size,
            number_of_streams=1,
            starting_stream_index=0,
            semaphore = None,
            numa_node = None,
            gpu_render_device = None):
        
        # create piperun config
        
        piperun_config_path = self._create_piperun_config(run_root, runner_config, number_of_streams)
        sinks = []
        sources = []
        for stream_index in range(number_of_streams):
            try:
                if (self._measurement_settings["scenario"]["source"]=="memory"):
                    os.unlink(self._input_paths[stream_index])
                os.unlink(self._output_paths[stream_index])
            except:
                pass

            if (self._measurement_settings["scenario"]["source"]=="memory"):
                os.mkfifo(self._input_paths[stream_index])
            os.mkfifo(self._output_paths[stream_index])

            # start read thread
            sink = MediaSink(self._output_paths[stream_index],
                             self._output_uris[stream_index],
                             self._output_caps[stream_index],
                             stream_index = stream_index + starting_stream_index,
                             reference_directory = os.path.join(self._args.workload_root,
                                                                "reference"),
                             warm_up = warm_up,
                             sample_size = sample_size,
                             save_pipeline_output = self._measurement_settings["save-pipeline-output"],
                             output_dir = os.path.dirname(piperun_config_path),
                             semaphore = semaphore,
                             daemon=True,
                             verbose_level=self._args.verbose_level)
            sink.start()
            sinks.append(sink)
        redirect = (self._args.verbose_level < 2)
        runner_process = start_pipeline_runner(self._args.runner,
                                               runner_config,
                                               run_root,
                                               piperun_config_path,
                                               self._pipeline.pipeline_root,
                                               os.path.join(self._args.workload_root,"systeminfo.json"),
                                               redirect,
                                               numa_node = numa_node,
                                               gpu_render_device = gpu_render_device,
                                               verbose_level=self._args.verbose_level)

        for stream_index in range(number_of_streams):
            # start writer thread
            if (self._measurement_settings["scenario"]["source"]=="memory"):
                source = MediaSource(self._input_paths[stream_index],
                                     self._input_uris[stream_index],
                                     self._input_caps[stream_index],
                                     elapsed_time = -1,
                                     frame_rate = frame_rate,
                                     input_directory=os.path.join(self._args.workload_root,"input"),daemon=True)
                source.start()
            else:
                source = None
            sources.append(source)
        
        return sources, sinks, runner_process
        
    def _load_reference(self, reference_target):
    
        reference = []

        reference_path = os.path.join(reference_target,"objects.jsonl")

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

    def _write_detection_reference(self, reference, reference_target):
        reference_path = os.path.join(reference_target, "detection.objects.jsonl")
        try:
            with open(reference_path,"w") as reference_file:
                for result in reference:
                    reference_file.write(json.dumps(result))
                    reference_file.write('\n')
        except Exception as error:
            print("Can't write reference! {}".format(error))

    
    def _remove_classifications(self, reference):
        for result in reference:
            if "objects" in result:
                for object_ in result["objects"]:
                    keys = list(object_.keys())
                    detection_keys = ["detection",'h','roi_type','w','x','y']
                    for key in keys:
                        if key not in detection_keys:
                            del object_[key]

    def _read_input_paths(self, input_directory):

        frame_paths = [ os.path.join(input_directory, path)
                         for path in os.listdir(input_directory) if path.endswith('bin')]
             
        frame_paths = [ frame_path for frame_path in frame_paths if os.path.isfile(frame_path) ]
        if len(frame_paths)>1:
            frame_paths.sort(key= lambda item: int(os.path.basename(item).split('_')[1].split('.')[0]))

        return frame_paths

     
    def prepare(self, workload_root, timeout):
        
        # todo resolve properties of task by filling in details from pipeline

        input_media_type = getattr(self._pipeline._namespace, "inputs.media.type.media-type")

        input_media = find_media(self._measurement_settings["media"], self._pipeline.pipeline_root, media_type_keys=[input_media_type])

        input_target = os.path.join(workload_root, "input")

        if not input_media:
            raise Exception("Media not found or unsupported: {}".format(self._measurement_settings["media"]))

        #if (self._args.force):
        create_directory(input_target)
        
        existing_files = [ file_path for file_path in os.listdir(input_target)
                           if os.path.isfile(os.path.join(input_target,file_path)) ]

        individual_frames = False
        
        if self._measurement_settings["scenario"]["source"] == "memory":
            individual_frames = True
        
        if (existing_files):
            print("Existing input, skipping generation")
        else:
            success, duration, target_fps = create_encoded_stream(input_target,
                                                                  input_media_type,
                                                                  input_media,
                                                                  individual_frames,
                                                                  target_fps = self._measurement_settings["target-fps"],
                                                                  duration = self._measurement_settings["duration"])
            self._measurement_settings["target-fps"] = target_fps
            self._measurement_settings["duration"] = duration

        input_paths = self._read_input_paths(input_target)

        models = self._get_models()
        if self._measurement_settings["generate-reference"]:
            reference_target = os.path.join(workload_root, "reference")

            output_media_type = self._output_media_type
            color_space = None
            resolution = None

            if "color-space" in self._pipeline._document:
                output_media_type+= ",format={}".format(self._pipeline._document["color-space"].upper())
                color_space = self._pipeline._document["color-space"].upper()
            if "resolution" in self._pipeline._document:
                output_media_type += ",height={},width={}".format(self._pipeline._document["resolution"]["height"],
                                                                  self._pipeline._document["resolution"]["width"])
                resolution = self._pipeline._document["resolution"]

            # Todo: get from task document
            existing_files = [ file_path for file_path in os.listdir(reference_target)
                               if os.path.isfile(os.path.join(reference_target,file_path)) ]

            if (existing_files):
                print("Existing reference, skipping generation")
            else:
                create_reference(input_target,
                                 reference_target,
                                 output_media_type,
                                 models,
                                 color_space = color_space,
                                 resolution = resolution,
                                 timeout=timeout,
                                 individual_frames=individual_frames)

            reference = self._load_reference(reference_target)

            for extra_input in input_paths[len(reference):]:
                try:
                    os.remove(extra_input)
                except Exception as error:
                    print(error)

            self._remove_classifications(reference)
            self._write_detection_reference(reference,reference_target)

    def _get_models(self):
        return []
    
    @classmethod
    def create_task(cls, measurement_settings, pipeline_path, args):
        if (not cls.task_map):
            cls.task_map = {}
            tasks = [task_class for task_class in Task.__subclasses__()]
            for task in tasks:
                for task_name in task.names:
                    cls.task_map[task_name] = task
                                        
        pipeline = PipelineConfig(pipeline_path, args)

        task = pipeline._task.get_task_scenario(measurement_settings["scenario"])

        task_name = pipeline._task.name

        return  cls.task_map[task_name](pipeline, task, measurement_settings, args)
        

    
