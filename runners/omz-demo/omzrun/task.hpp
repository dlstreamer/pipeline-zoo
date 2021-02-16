#pragma once
#include "yaml-cpp/yaml.h"
#include <nlohmann/json.hpp>
#include <memory>
#include "opencv2/core/utils/filesystem.hpp"
#include <fstream>
#include <opencv2/gapi/imgproc.hpp>
#include "opencv2/core/utils/logger.hpp"
#include "modelutil.hpp"
#include "models/detection_model_ssd.h"
#include "pipelines/async_pipeline.h"
#include "pipelines/config_factory.h"
#include <gflags/gflags.h>
#include <samples/images_capture.h>
#include <samples/default_flags.hpp>
#include "pipelines/metadata.h"
#include <sys/stat.h>
#include <libgen.h>

#define NANOSECONDS_IN_SECONDS 1000000000L


using json = nlohmann::json;

namespace task {

  struct Avg {
    struct Elapsed {
        explicit Elapsed(double ms) : ss(ms/1000.), mm(static_cast<int>(ss)/60) {}
        const double ss;
        const int    mm;
    };

    using MS = std::chrono::duration<double, std::ratio<1, 1000>>;
    using TS = std::chrono::time_point<std::chrono::high_resolution_clock>;
    TS started;

    void    start() { started = now(); }
    TS      now() const { return std::chrono::high_resolution_clock::now(); }
    double  tick() const { return std::chrono::duration_cast<MS>(now() - started).count(); }
    Elapsed elapsed() const { return Elapsed{tick()}; }
    double  fps(std::size_t n) const { return static_cast<double>(n) / (tick() / 1000.); }
};

std::ostream& operator<<(std::ostream &os, const Avg::Elapsed &e) {
    os << e.mm << ':' << (e.ss - 60*e.mm);
    return os;
}


  template<class T>
  void set_default(YAML::Node node,
		   const std::string &key,
		   T value) {
    if (!node[key]) {
      node[key] = value;
    }
  }

  
  struct Task
  {
    virtual ~Task() = default;
    static std::unique_ptr<Task> Create(YAML::Node &config);
    virtual void init() = 0;
    virtual void run() = 0;
    virtual void log_details() = 0;
    virtual bool export_cmdline(std::string path){return false;};
  };
  
  class ObjectDetection: public Task {
    
  protected:
    
    YAML::Node &_config;
    modelutil::ModelParameters _detection_model_params;
    std::vector<modelutil::ModelParameters> _classification_models;
    json _attribute_postproc;

    std::string _source;
    std::string _destination;
    uint64_t _frame_duration_ns;
    std::string _source_path;
    std::string _detect_model_config;
    std::unique_ptr<ModelBase> _detection_model;
    InferenceEngine::Core core;

    void _set_detection_model(const std::string& detect_model_config) {

      // detection network
      find_model(this->_config,
		 this->_config["pipeline"][detect_model_config].as<std::string>(),
		 this->_detection_model_params);

      auto converter = this->_detection_model_params.proc["output_postproc"][0]["converter"];
      
      if ( converter != "tensor_to_bbox_ssd" ) {
	std::cout << "Post Proc" << converter << "Not Supported" << std::endl;
	throw "unsupported";
      }

      auto runner_config = this->_config["runner-config"];
      
      set_default(runner_config,
			"detect",YAML::Node());

      set_default(runner_config["detect"],
			"device",
			"CPU");

      set_default(runner_config["detect"],
		  "precision",
		  "");

      set_default(runner_config["detect"],
			"threshold",
			0.5);

      set_default(runner_config["detect"],
			"auto-resize",
			false);
      
      set_default(runner_config["detect"],
			"custom-cpu-library",
			"");

      set_default(runner_config["detect"],
			"custom-cldnn-library",
			"");

      set_default(runner_config["detect"],
		  "performance-counters",
		  false);

      set_default(runner_config["detect"],
		  "nireq",
		  2);

      set_default(runner_config["detect"],
		  "nthreads",
		  0);

      set_default(runner_config["detect"],
		  "nstreams",
		  "");
      
      auto device = runner_config["detect"]["device"].as<std::string>();
      auto precision = runner_config["detect"]["precision"].as<std::string>();
      
      auto labels = this->_detection_model_params.proc["output_postproc"][0]["labels"];
      if (labels != nullptr) {
	this->_detection_model.reset(new ModelSSD(this->_detection_model_params.network(device, precision),
						runner_config["detect"]["threshold"].as<float>(),
						runner_config["detect"]["auto-resize"].as<bool>(),
						labels));
      }
      else {
	this->_detection_model.reset(new ModelSSD(this->_detection_model_params.network(device, precision),
						  runner_config["detect"]["threshold"].as<float>(),
						  runner_config["detect"]["auto-resize"].as<bool>()));
      }
      printf("%s\n",this->_detection_model->getModelFileName().c_str());
    }
    
    
  public:

        
    ObjectDetection(YAML::Node &config,
		    const std::string& detect_model_config="model"):_config(config),
								    _source(this->_create_source_string()),
								    _destination(this->_create_destination_string()),
								    _source_path(this->_get_source_path()),
								    _detect_model_config(detect_model_config) {
      this->_set_detection_model(this->_detect_model_config);

    }
    
    void init() {}

    std::string _create_decode_string(const std::string &media_type) {

      std::ostringstream result;
      auto config = this->_config["runner-config"];
      
      static std::map<const std::string, std::map<const std::string, const std::string > > media_type_map
	= {
	   {"video/x-h264",{{"CPU","avdec_h264"},
			    {"GPU","vaapih264dec"}}
	   }
      };
      
      set_default(config,
			"decode",YAML::Node());

      set_default(config["decode"],
			"device",
			"CPU");

      auto device = config["decode"]["device"].as<std::string>();
      
      std::map<const std::string, const std::string> device_map = { {"CPU","decodebin"},
								    {"GPU","vaapidecodebin"}};
      auto media_type_iterator = media_type_map.find(media_type);
      if (media_type_iterator != media_type_map.end()) {
        device_map = media_type_iterator->second;
      }

      set_default(config["decode"],
			"element",
			device_map[device]);
      
      result << config["decode"]["element"] << " ";

      for (auto i : config["decode"]) {
	if ((i.first.as<std::string>()!="element") && (i.first.as<std::string>()!="device")) {
	  result << i.first << "=" << i.second << " ";
	}
      }
      return result.str();
    }

    std::string _create_destination_string() {
      auto output_uri = this->_config["outputs"][0]["uri"].as<std::string>();
      auto scheme_end = output_uri.find("://");
      auto scheme = output_uri.substr(0,scheme_end);      
      auto path = output_uri.substr(scheme_end+3,
					  std::string::npos);
      if (scheme != "pipe") {
	std::cout << "Scheme not Supported!" << "\n";
	throw "Scheme not Supported!";
      }
      return path;
    }

    std::string _create_videoconvert() {
      std::ostringstream result;
      auto config = this->_config["runner-config"];
      set_default(config["convert"],"n-threads",cv::getNumThreads());
      result << "videoconvert name=convert n-threads=" << config["convert"]["n-threads"];
      return result.str();
    }
    
    std::string _create_appsink() {
      std::ostringstream result;
      result << "appsink sync=false emit-signals=false";
      return result.str();
    }


    std::string _get_source_path() {
      auto input_uri = this->_config["inputs"][0]["uri"].as<std::string>();
      auto scheme_end = input_uri.find("://");
      auto scheme = input_uri.substr(0,scheme_end);      
      return input_uri.substr(scheme_end+3,
			      std::string::npos);
    }
    
    std::string _create_source_string() {

      std::ostringstream result;

      static std::map<const std::string, const std::string> scheme_map = {
							      {"pipe","filesrc"},
							      {"file","filepath"},
							      {"rtsp","rtspsrc"}
      };

      auto input_uri = this->_config["inputs"][0]["uri"].as<std::string>();
      auto scheme_end = input_uri.find("://");
      auto scheme = input_uri.substr(0,scheme_end);      
      auto path = input_uri.substr(scheme_end+3,
					  std::string::npos);
      set_default(this->_config["inputs"][0],
			"caps",
			"");
      auto caps = this->_config["inputs"][0]["caps"].as<std::string>();
      auto media_type_end = caps.find(",");
      auto media_type = caps.substr(0,media_type_end);
      int framerate_numerator = 30;
      int framerate_denominator = 1;
      auto framerate = caps.find("framerate=(fraction)");
      if (framerate != std::string::npos) { 
	std::sscanf(caps.substr(caps.find("framerate=(fraction)"), std::string::npos).c_str(),
		    "framerate=(fraction)%d/%d",
		    &framerate_numerator,
		    &framerate_denominator);
      }
      this->_frame_duration_ns = uint64_t((float(framerate_denominator)/float(framerate_numerator) *
					   NANOSECONDS_IN_SECONDS));
      
      
      if (input_uri == scheme) {
	std::cout << "Scheme Not Found" << "\n";
	throw "Scheme Not Found";
      }

      auto source_iterator = scheme_map.find(scheme);
      if (source_iterator == scheme_map.end()) {
	result << "urisourcebin";
      } else {
	result << source_iterator->second;
      }

      if (result.str() == "filepath") {
	return path;
      }

      if (result.str() == "filesrc") {
	if (scheme == "pipe") {
	  result << " location=\"" << path << "\" ! video/x-h264 ! h264parse";
	
	}
	if (scheme =="file") {
	  result << " location=\"" << path << "\" ";	
	}
	
      }

      if (caps != "") {
      	result << " ! " << caps;
      }
      
      result << " ! " << _create_decode_string(media_type)
	     << " ! " << _create_videoconvert()
	     << " ! video/x-raw,format=BGR"
	     << " ! " << _create_appsink();

      
      
      return result.str();

    }

    json detection_result_to_json(std::unique_ptr<ResultBase> &_detection_result,
				  int frame_index) {
      json result;
      ImageMetaData &metadata = _detection_result->metaData->asRef<ImageMetaData>();

      DetectionResult* detection_result = (DetectionResult*)_detection_result.get();
      
      result["resolution"] = { {"height", metadata.img.size().height},
			       {"width", metadata.img.size().width} };
      
      result["timestamp"] = frame_index * this->_frame_duration_ns;
      result["source"] = this->_source_path;

      for (auto object : detection_result->objects) {
	float x_max = (float)(object.x + object.width) / (float)metadata.img.size().width;
	float x_min = (float)(object.x)/(float)metadata.img.size().width;
	float y_min = (float)(object.y)/(float)metadata.img.size().height;
	float y_max = (float)(object.y + object.height) / (float)metadata.img.size().height;
	
	json detection = { {"bounding_box",{"x_max",x_max,
					    "x_min",x_min,
					    "y_min",y_min,
					    "y_max",y_max}},
			   {"confidence",object.confidence},
			   {"label",object.label},
			   {"label_id",object.labelID}};

	json json_object = { {"detection", detection},
			     {"h", object.height},
			     {"w", object.width},
			     {"x", object.x},
			     {"y", object.y} };
	
	result["objects"].push_back(json_object);
      }
      return result;
    }


    void log_details() {
      std::cout << std::endl << std::endl;
      std::string header(30, '*');
      std::cout << header << std::endl;
      std::cout << "OMZRUN" << std::endl;
      std::cout << header << std::endl;
      std::cout << "Task:\t" <<this->_config["pipeline"]["task"] << std::endl;
      std::cout << "Detection Model:\t" << this->_detection_model_params.name << std::endl << std::endl;
      std::cout << "\t" << this->_detection_model_params << std::endl;
      for (auto model : this->_classification_models) {
	std::cout << "Classification Model:\t" <<  model.name;
	std::cout << "\t" << model << std::endl;
      }
      std::cout << "CaptureSource:\n\t" <<this->_source << std::endl << std::endl;
      std::cout << header << std::endl << std::endl;
    }

    bool exists(const std::string &path) {
      struct stat unused;
      return (stat(path.c_str(),&unused)==0);
    }
    
    bool export_cmdline(std::string path) {
      auto runner_config = this->_config["runner-config"];
      auto detect = runner_config["detect"];

      auto executable = this->_config["pipeline-root"].as<std::string>() +
	"/runners/omz-demo/omz_demos_build/intel64/Release/object_detection_demo";
			    
      if (!exists(executable)) {
	return false;
      }

      auto labels = this->_detection_model_params.proc["output_postproc"][0]["labels"];
      if (labels != nullptr) {
	std::vector<std::string> labels_vector = this->_detection_model_params.proc["output_postproc"][0]["labels"];
      
	auto labels_path = std::string(dirname((char*)this->_detection_model_params.proc_path.c_str())) + "/labels.txt";
	FILE* labels_file = fopen(labels_path.c_str(),"w");

	if (! labels_file) {
	  return false;
	}
      
	for (auto label : labels_vector) {
	  fputs((label +"\n").c_str(),labels_file);
	}
	fclose(labels_file);
	executable.append(" -labels " + labels_path);
      }
      
      auto device = runner_config["detect"]["device"].as<std::string>();
      auto precision = runner_config["detect"]["precision"].as<std::string>();
      
      executable.append(" -i "+ this->_config["inputs"][0]["source"].as<std::string>());
      executable.append(" -m "+ this->_detection_model_params.network(device, precision));
      executable.append(" -d "+ device);

      if (detect["custom-cpu-library"].as<std::string>()!="") {
	executable.append(" -l " + detect["custom-cpu-library"].as<std::string>());
      }
      
      if (detect["custom-cldnn-library"].as<std::string>()!="") {
	executable.append(" -c " + detect["custom-cldnn-library"].as<std::string>());
      }

      executable.append(" -nireq " + std::to_string(detect["nireq"].as<int>()));
      executable.append(" -nthreads " + std::to_string(detect["nthreads"].as<int>()));
      executable.append(" -t " + std::to_string(detect["threshold"].as<float>()));

      if (detect["nstreams"].as<std::string>()!="") {
	executable.append(" -nstreams " + detect["nstreams"].as<std::string>());
      }

      if (detect["performance-counters"].as<bool>()) {
	executable.append(" -pc");
      }
      
      if (detect["auto-resize"].as<bool>()) {
	executable.append(" -auto_resize");
      }
	
      executable.append(" -at ssd");
      executable.append(" -no_show");

      FILE * command_file = fopen(path.c_str(),"w");
      if (! command_file) {
	return false;
      }
      fputs("#!/bin/bash\n\n",command_file);
      fputs(("\necho '\n\n" + executable+"\n\n'\n\n").c_str(),command_file);
      fputs((executable+"\n").c_str(),command_file);
      fclose(command_file);
      chmod(path.c_str(),S_IXGRP | S_IXOTH | S_IEXEC | S_IWUSR | S_IROTH | S_IRUSR);
      return true;
    }

    void run() {

      auto runner_config = this->_config["runner-config"];
      auto detect = runner_config["detect"];
      
      AsyncPipeline pipeline(std::move(this->_detection_model),
			     ConfigFactory::getUserConfig(detect["device"].as<std::string>(),
							  detect["custom-cpu-library"].as<std::string>(),
							  detect["custom-cldnn-library"].as<std::string>(),
							  detect["performance-counters"].as<bool>(),
							  detect["nireq"].as<int>(),
							  detect["nstreams"].as<std::string>(),
							  detect["nthreads"].as<int>()),
			     this->core);
      

      auto cap = openImagesCapture(this->_source,false);
      bool running = true;
      Avg avg;
      std::size_t frames = 0u;
      std::ofstream fout(this->_destination,
			 std::ios::out);
      cv::Mat frame;
      std::unique_ptr<ResultBase> result;
      avg.start();
      
      while (running) {
	if (pipeline.isReadyToProcess()) {
	  auto startTime = std::chrono::steady_clock::now();
	  frame = cap->read();
	  if (frame.empty()) {
	    if (frames==0) {
	      throw std::logic_error("Can't read image from input");
	    }
	    else {
	      break;
	    }
	  }

	  pipeline.submitData(ImageInputData(frame),
			      std::make_shared<ImageMetaData>(frame,startTime));
	}
	pipeline.waitForData();
	while((result=pipeline.getResult()) && running) {
	  fout << detection_result_to_json(result, frames) << '\n';
	  fout.flush();
	  
	  if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_VERBOSE) {
	    std::cout << detection_result_to_json(result, frames) << std::endl;  
	  }
	  frames++;
	  if (frames % 50 == 0) {
	    if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_INFO) {
	      std::cout << "frames: " << frames << " fps: " << avg.fps(frames) << std::endl;
	    }
	  }
	  
	}
      }

      if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_INFO) {
	std::cout << "Total frames: " << frames << " fps: " << avg.fps(frames) << std::endl;
      }      	
    }
  };

  
  std::unique_ptr<Task> Task::Create(YAML::Node &config)
  {
    if (config["pipeline"]["task"].as<std::string>()=="object-detection") {
      return std::unique_ptr<ObjectDetection>(new ObjectDetection(config));
    }  
    else {
      return NULL;
    }
    
  }

}
