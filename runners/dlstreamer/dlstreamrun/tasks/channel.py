import os
import copy

from tasks.task import input_to_src
from tasks.task import decode_properties
from tasks.task import output_to_sink
from tasks.task import find_model
from tasks.task import queue_properties
from tasks.task import inference_properties
from tasks.task import vpp_properties
from tasks.task import overlay_properties

class Channel():

    def __init__(self, runner_config, model_root, system_info, caps, channel_number):
        self._runner_config = runner_config
        self.channel_number = channel_number
        self.system_info = system_info
        self.model_root = model_root

        self._elements = []

    def add_detect_element(self, detect_model_name):
        self._detect_model_name = detect_model_name
        self._runner_config.setdefault("detect",{})
        self._runner_config["detect"].setdefault("element","gvadetect")
        self._runner_config["detect"].setdefault("name", "detect" + str(self.channel_number))
        self._runner_config["detect"].setdefault("enabled",True)
 
        self._model = find_model(detect_model_name, self.model_root, None)

        queue_name = "detect-queue"
        queue_config = self._runner_config.setdefault(queue_name,{})
        queue_config.setdefault("element", "queue")
        queue_config.setdefault("name", queue_name+str(self.channel_number))
        queue_config.setdefault("enabled", False)

        self._detect_queue_properties = queue_properties(queue_config,
                                                            self._model,
                                                            self.system_info)

        self._detect_properties = inference_properties(self._runner_config["detect"],
                                                        self._model,
                                                        detect_model_name,
                                                        self.system_info)

        self._elements.append(self._detect_queue_properties)
        self._elements.append(self._detect_properties)

    def add_classify_element(self, classify_model_config):
        self.classify_model_config = classify_model_config
        self._classify_properties = self._set_classify_properties(self.model_root, self.system_info, detect_model_name=self._detect_model_name,
                                                                  channel_number=self.channel_number)

        self._elements.append(self._classify_properties)
        
    def add_multi_detect_element(self, multi_detect_model_config):
        self.multi_detect_model_config = multi_detect_model_config
        self._multi_detect_properties = self._set_multi_detect_properties(self.model_root, self.system_info, detect_model_name=self._detect_model_name,
                                                                  channel_number=self.channel_number)

        self._elements.append(self._multi_detect_properties)

    def add_inference_element(self, inference_model_config):
        self.inference_model_config = inference_model_config
        self._inference_properties = self._set_inference_properties(self.model_root, self.system_info, detect_model_name=self._detect_model_name,
                                                                  channel_number=self.channel_number)

        print("inference properties: {}".format(self._inference_properties))
        self._elements.append(self._inference_properties)

    def add_barcode_detector_element(self, barcode_config):
        # if the datatype of barcode_config is bool and set to False
        if (isinstance(barcode_config, bool) and (not barcode_config)):
            return
        self._barcode_detect = "opencv_barcode_detector "
        properties = ""
        if (isinstance(barcode_config, dict) and barcode_config):
            properties_list = ["{}={}".format(key,value) for key,value in barcode_config.items()]
            properties = " ".join(properties_list)
        self._barcode_detect += properties 
        self._elements.append(self._barcode_detect)

    def add_src_element(self, input):
        self.input = input
        self._src_element = input_to_src(input)

    def add_caps_element(self, caps):
        self._caps = caps

    def add_sink_element(self, output, overlay_pipeline=None, run_directory=None):
        self._sink_element = output_to_sink(output,
                                            self._runner_config,
                                            self.channel_number,
                                            overlay_pipeline,
                                            run_directory)

    def add_decode_element(self):
        self._runner_config.setdefault("decode", {"device":"CPU"})
        queue_name = "decode-queue"
        queue_config = self._runner_config.setdefault(queue_name,{})

        self._decode_properties = decode_properties(self._runner_config["decode"],
                                                        queue_config,
                                                        self.input,
                                                        self.system_info, self.channel_number)

        self._elements.append(self._decode_properties)

        if ("msdk" in self._decode_properties):
                self._caps = self.input["extended-caps"]

    def get_overlay_pipeline(self):
        self._runner_config.setdefault("overlay", {"device":"GPU"})
        queue_name = "overlay-queue"
        queue_config = self._runner_config.setdefault(queue_name,{})
        return overlay_properties(self._runner_config["overlay"],
                                                        queue_config,
                                                        self.input,
                                                        self.system_info, self.channel_number)

    def add_meta_element(self):
        self._meta_element = "gvametaconvert add-empty-results=true ! gvametapublish method=file file-format=json-lines file-path=/tmp/result.jsonl"


    def add_fpscounter_element(self):
        self._fpscounter = "gvafpscounter"

    def add_fakesink_element(self):
        self._fakesink = "fakesink async=false"

    def add_multifilesink_element(self):
        self._multifilesink = "multifilesink location=\"%d.bin\""

    def add_vpp_element(self, color_space, region, resolution):
        self._runner_config.setdefault("vpp",{"device":"CPU"})
        vpp_queue_name = "vpp-queue"
        vpp_queue_config = self._runner_config.setdefault(vpp_queue_name,{})
        self._vpp_properties = vpp_properties(self._runner_config["vpp"],
                                              vpp_queue_config,
                                              color_space,
                                              region,
                                              resolution,
                                              self.system_info,
                                              self.channel_number)

        self._elements.append(self._vpp_properties)

    def get_channel_standalone_pipeline(self):
        standalone_elements = self._create_standalone_elements()

        standalone_elements = " ! ".join([element for element in standalone_elements if element])

        return standalone_elements

    def get_channel_pipeline(self):

        elements = self._create_elements()
        elements = " ! ".join([element for element in elements if element])

        return elements

    def _create_elements(self):
        return [self._src_element, self._caps] + self._elements + [self._sink_element]

    def _create_standalone_elements(self):

        demux = ( "qtdemux" if os.path.splitext(
            self.input["source"])[1]==".mp4" else "")
        
        res = ["urisourcebin uri=file://{}".format(self.input["source"]), demux, "parsebin"] + self._elements
        
        if hasattr(self, '_barcode_detect'):
            res = res + [self._barcode_detect]

        if hasattr(self, '_meta_element'):
            res = res + [self._meta_element]

        if hasattr(self, '_fpscounter'):
            res = res + [self._fpscounter]

        if hasattr(self, '_fakesink'):
            res = res + [self._fakesink]

        if hasattr(self, '_multifilesink'):
            res = res + [self._multifilesink]
        
        return res

    def _set_inference_properties(self, model_root, system_info, detect_model_name="", channel_number=0):
        result = ""
        elements = []

        if not self.inference_model_config:
            return result
        
        inference_model_list = self.inference_model_config
        for index, model_name in enumerate(inference_model_list):
            if (isinstance(model_name,list)):
                raise Exception("Dependent Inference Not Supported")
            model = find_model(model_name,
                                model_root,
                                None)

            element_name = "inference-{}".format(index)
            inference_config = self._runner_config.setdefault(element_name, {})
            inference_config.setdefault("element", "gvainference")
            inference_config.setdefault("name",element_name+str(channel_number))
            inference_config.setdefault("enabled", True)

            if detect_model_name=="full_frame":
                inference_config.setdefault("inference-region", "full-frame")

            queue_name = "inference-{}-queue".format(index)
            queue_config = self._runner_config.setdefault(queue_name,{})
            queue_config.setdefault("element", "queue")
            queue_config.setdefault("name", queue_name+str(channel_number))
            queue_config.setdefault("enabled", inference_config["enabled"])
            elements.append(queue_properties(queue_config,
                                                model,
                                                system_info))

            elements.append(inference_properties(inference_config,
                                                    model,
                                                    model_name,
                                                    system_info))
        if (elements):
            result = " ! ".join([element for element in elements if element])
            
        return result

    def _set_classify_properties(self, model_root, system_info, detect_model_name="", channel_number=0):
        result = ""
        elements = []
        if (self.classify_model_config):
            classify_model_list = self.classify_model_config
            for index, model_name in enumerate(classify_model_list):
                if (isinstance(model_name,list)):
                    raise Exception("Dependent Classification Not Supported")
                model = find_model(model_name,
                                   model_root,
                                   None)
                element_name = "classify-{}".format(index)
                classify_config = self._runner_config.setdefault(element_name,
                                                                 {})
                classify_config.setdefault("element","gvaclassify")
                classify_config.setdefault("name",element_name+str(channel_number))
                classify_config.setdefault("enabled", True)

                if detect_model_name=="full_frame":
                    classify_config.setdefault("inference-region", "full-frame")

                queue_name = "classify-{}-queue".format(index)
                queue_config = self._runner_config.setdefault(queue_name,{})
                queue_config.setdefault("element", "queue")
                queue_config.setdefault("name", queue_name+str(channel_number))
                queue_config.setdefault("enabled", classify_config["enabled"])
                
                elements.append(queue_properties(queue_config,
                                                 model,
                                                 system_info))
                elements.append(inference_properties(classify_config,
                                                     model,
                                                     model_name,
                                                     system_info))
            if (elements):
                result = " ! ".join([element for element in elements if element])
            
        return result

    def add_track_element(self, assign_config):
        self.assign_config = assign_config

        self._assign_properties = self._set_track_properties(channel_number=self.channel_number)
        self._elements.append(self._assign_properties)

    def _set_track_properties(self, channel_number=0):
        result = ""
        elements = []

        element_name = "track"
        track_config = self._runner_config.setdefault(element_name, {})

        print("Track CONFIG: " + str(track_config.items()))

        properties = ["{}={}".format(key,value) for key,value in track_config.items()]

        elements.append("python_object_association object-class=\"{}\" {}".format(self.assign_config, " ".join(properties)))

        if (elements):
                result = " ! ".join([element for element in elements if element])
            
        return result
    
    def _set_multi_detect_properties(self, model_root, system_info, detect_model_name="", channel_number=0):
        result = ""
        elements = []
        if (self.multi_detect_model_config):
            detection_model_list = self.multi_detect_model_config
            for index, model_name in enumerate(detection_model_list):
                if (isinstance(model_name,list)):
                    raise Exception("Dependent Classification Not Supported")
                model = find_model(model_name,
                                   model_root,
                                   None)
                element_name = "detect-{}".format(index)
                detect_config = self._runner_config.setdefault(element_name,
                                                                 {})
                detect_config.setdefault("element","gvadetect")
                detect_config.setdefault("name",element_name+str(channel_number))
                detect_config.setdefault("enabled", True)

                if detect_model_name=="full_frame":
                    detect_config.setdefault("inference-region", "full-frame")
                else:
                    detect_config.setdefault("inference-region", "roi-list")
                    
                queue_name = "detect-{}-queue".format(index)
                queue_config = self._runner_config.setdefault(queue_name,{})
                queue_config.setdefault("element", "queue")
                queue_config.setdefault("name", queue_name+str(channel_number))
                queue_config.setdefault("enabled", detect_config["enabled"])
                
                elements.append(queue_properties(queue_config,
                                                 model,
                                                 system_info))
                elements.append(inference_properties(detect_config,
                                                     model,
                                                     model_name,
                                                     system_info))
            if (elements):
                result = " ! ".join([element for element in elements if element])
            
        return result
