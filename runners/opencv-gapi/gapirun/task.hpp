#pragma once
#include "yaml-cpp/yaml.h"
#include <nlohmann/json.hpp>
#include <memory>
#include "opencv2/core/utils/filesystem.hpp"
#include "postproc.hpp"
#include <fstream>
#include <opencv2/gapi/imgproc.hpp>
#include "opencv2/core/utils/logger.hpp"
#include "modelutil.hpp"

#define NANOSECONDS_IN_SECONDS 1000000000


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
  };
  
  class ObjectDetection: public Task {
    
  protected:
    
    YAML::Node &_config;
    modelutil::ModelParameters _detection_model;
    std::vector<modelutil::ModelParameters> _classification_models;
    json _attribute_postproc;
    cv::GStreamingCompiled _pipeline;

    std::string _source;
    std::string _destination;
    int _frame_height;
    int _frame_width;
    uint64_t _frame_duration_ns;
    std::string _source_path;
    std::string _detect_model_config;
    
    using ClassificationModels = std::vector<cv::gapi::ie::Params<modelutil::Classifications>>;
    using ClassificationTwoLayerModels = std::vector<cv::gapi::ie::Params<modelutil::ClassificationsTwoLayers>>;

    std::tuple<ClassificationModels,ClassificationTwoLayerModels> _get_classification_params() {
      ClassificationModels classification_models;
      ClassificationTwoLayerModels classification_two_layer_models;

      set_default(this->_config["pipeline"],"classification-models",YAML::Node());
      int index = 0;
      for (auto model_name : this->_config["pipeline"]["classification-models"]) {
	
	modelutil::ModelParameters model;
	std::string config_name = "classify-" + std::to_string(index);
	  
	find_model(this->_config,
		   model_name.as<std::string>(),
		   model);

	this->_classification_models.push_back(model);

	auto runner_config = this->_config["runner-config"];
	
	set_default(runner_config,
		    config_name,YAML::Node());
	
	set_default(runner_config[config_name],
		    "device",
		    "CPU");

	auto device = runner_config[config_name]["device"].as<std::string>();
	
	if ( model.proc["output_postproc"].size() == 1) {
	  classification_models.push_back(model.params<modelutil::Classifications>(device));
	} else if (model.proc["output_postproc"].size() == 2) {
	  std::array<std::string,2> layer_names {
						 model.proc["output_postproc"][0]["layer_name"],
						 model.proc["output_postproc"][1]["layer_name"]
	  };
	  classification_two_layer_models.push_back(model.params<modelutil::ClassificationsTwoLayers>(device).cfgOutputLayers(layer_names));
	       
	} else {
	  std::cout << "Post Proc" << model.proc["output_postproc"] << "Not Supported" << std::endl;
	  throw "unsupported";
	}
	index++;
      }

      for (auto model: this->_classification_models) {
	if (model.proc["output_postproc"].size() == 1) {
	  for (auto postproc : model.proc["output_postproc"]) {
	    postproc["model_name"] = model.name;
	    this->_attribute_postproc.push_back(postproc);
	  }
	}
      }
      for (auto model: this->_classification_models) {
	if (model.proc["output_postproc"].size() == 2) {
	  for (auto postproc : model.proc["output_postproc"]) {
	    postproc["model_name"] = model.name;
	    this->_attribute_postproc.push_back(postproc);
	  }
	}
      }
      return std::make_tuple(classification_models, classification_two_layer_models);
    }


    cv::gapi::ie::Params<modelutil::Detections> _get_detection_params(const std::string& detect_model_config) {
      // detection network
      find_model(this->_config,
		 this->_config["pipeline"][detect_model_config].as<std::string>(),
		 this->_detection_model);

      auto converter = this->_detection_model.proc["output_postproc"][0]["converter"];
      
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
      
      auto device = runner_config["detect"]["device"].as<std::string>();

    
      return this->_detection_model.params<modelutil::Detections>(device);

    }

    cv::gapi::GNetPackage _get_network_params(const std::string& detect_model_config) {

      auto det_net = this->_get_detection_params(detect_model_config);
      auto classification_networks= this->_get_classification_params(); 
      auto networks = cv::gapi::networks();
      networks.networks.push_back(cv::gapi::GNetParam{det_net.tag(),
      						det_net.backend(),
      						det_net.params()});

      auto classification_nets = std::get<0>(classification_networks);
      for (auto network : classification_nets) {
	networks.networks.push_back(cv::gapi::GNetParam{network.tag(),
							  network.backend(),
							  network.params()});

      }
      auto classification_two_layer_nets = std::get<1>(classification_networks);
      for (auto network : classification_two_layer_nets) {
	networks.networks.push_back(cv::gapi::GNetParam{network.tag(),
							  network.backend(),
							  network.params()});
	
      }
      return networks;
    }

    virtual cv::GComputation graph() {
        cv::GComputation graph([]() {
			    // Declare an empty GMat - the beginning of the pipeline.
			    cv::GMat in;
			    
			    // Run object detection on the input frame. Result is a single GMat,
			    // internally representing an 1x1x200x7 SSD output.
			    // This is a single-patch version of infer:
			    // - Inference is running on the whole input image;
			    // - Image is converted and resized to the network's expected format
			    //   automatically.
			    cv::GMat detections = cv::gapi::infer<modelutil::Detections>(in);

			    // Parse SSD output to a list of ROI (rectangles) using
			    // a custom kernel. Note: parsing SSD may become a "standard" kernel.

			    cv::GArray<cv::Rect> regions;
			    cv::GArray<postproc::ObjectDetectionResult> objects;
			    
			    objects = postproc::SSDPostProc::on(detections,in);
			    regions = postproc::ExtractRegions::on(objects);
			    
			    // Now specify the computation's boundaries - our pipeline consumes
			    // one images and produces five outputs.
			    return cv::GComputation(cv::GIn(in),
						    cv::GOut(objects, regions));

			  });
	return graph;
    }
    
  public:

        
    ObjectDetection(YAML::Node &config,
		    const std::string& detect_model_config="model"):_config(config),
								    _source(this->_create_source_string()),
								    _destination(this->_create_destination_string()),
								    _source_path(this->_get_source_path()),
								    _detect_model_config(detect_model_config) {}
    
    void init() {

      auto kernels = cv::gapi::kernels<postproc::OCVSSDPostProc, postproc::OCVExtractRegions>();

      auto networks = this->_get_network_params(this->_detect_model_config);
      
      this->_pipeline = this->graph().compileStreaming(cv::compile_args(kernels, networks));

    }

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
							      {"file","filesrc"},
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
      int framerate_numerator;
      int framerate_denominator;
      std::sscanf(caps.substr(caps.find("framerate=(fraction)"), std::string::npos).c_str(),
			      "framerate=(fraction)%d/%d",
			      &framerate_numerator,
			      &framerate_denominator);
      
      this->_frame_duration_ns = uint64_t((float(framerate_denominator)/float(framerate_numerator) *
					   NANOSECONDS_IN_SECONDS));
      
      std::sscanf(caps.substr(caps.find("width=(int)"),std::string::npos).c_str(),
		  "width=(int)%d",
		  &this->_frame_width);
      
      std::sscanf(caps.substr(caps.find("height=(int)"),std::string::npos).c_str(),
		  "height=(int)%d",
		  &this->_frame_height);

      
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

    json &attribute_to_json(cv::Mat attribute,
			    int attribute_index,
			    json &object) {
      auto postproc = this->_attribute_postproc[attribute_index];
      
      json &json_attribute = object[postproc["attribute_name"].get<std::string>()];
      
      json_attribute["model"] = {{"name", postproc["model_name"]}};
      const float* results = attribute.ptr<float>();
      if (postproc["converter"] == "tensor_to_label") {
	if (postproc["method"] == "max") {
	  const float* end = results + attribute.total();
	  if (postproc["labels"].size()>0) {
	    end = results + postproc["labels"].size();
	  }
	  const auto label_id = std::max_element(results, end) - results;
	  if (postproc["labels"].size()>0) {
	    json_attribute["label"] = postproc["labels"][label_id];
	  } else {
	    json_attribute["label_id"] = label_id;
	  }
	}
      } else if (postproc["converter"] == "tensor_to_text") {
        float scale = 1;
	int precision = 0;
	if (postproc.find("tensor_to_text_scale") != postproc.end()) {
	  scale = postproc["tensor_to_text_scale"];
	}
	if (postproc.find("tensor_to_text_precision") != postproc.end()) {
	  precision = postproc["tensor_to_text_precision"];
	}
	std::ostringstream label;
	label << std::fixed << std::setprecision(precision) << (scale * results[0]);
	json_attribute["label"] = label.str();
      } else {
	std::cout << "Unknown Converter: " << postproc["converter"] << std::endl;
	throw "Unknown Converter"; 
      }
      return json_attribute;
    }

    template<unsigned int N>
    json objects_to_json(const std::vector<postproc::ObjectDetectionResult> &objects,
			 const std::array<std::vector<cv::Mat>,N>& attributes,
			 int frame_index) {
      json result;
      result["resolution"] = { {"height", this->_frame_height},
			       {"width", this->_frame_width} };

      result["timestamp"] = frame_index * this->_frame_duration_ns;
      result["source"] = this->_source_path;
      int object_index = 0;
      for (auto object : objects) {
	auto label = this->_detection_model.proc["output_postproc"][0]["labels"][int(object.object_type)];

	json detection = { {"bounding_box", {"x_max",object.roi_right,
					     "x_min",object.roi_left,
					     "y_min",object.roi_top,
					     "y_max",object.roi_bottom}},
			   {"confidence",object.confidence},
			   {"label",label},
			   {"label_id",object.object_type}};
	
	json json_object = { {"detection", detection},
			     {"h", object.roi.height},
			     {"w", object.roi.width},
			     {"x", object.roi.x},
			     {"y", object.roi.y} };
	
	int attribute_index = 0;
	for (auto attribute : attributes) {

	  this->attribute_to_json(attribute[object_index],
				  attribute_index,
				  json_object);
	  ++attribute_index;
	}

	result["objects"].push_back(json_object);
	++object_index;
      }
      return result;
    }

    void log_details() {
      std::cout << std::endl << std::endl;
      std::string header(30, '*');
      std::cout << header << std::endl;
      std::cout << "GAPI-RUN" << std::endl;
      std::cout << header << std::endl;
      std::cout << "Task:\t" <<this->_config["pipeline"]["task"] << std::endl;
      std::cout << "Detection Model:\t" << this->_detection_model.name << std::endl << std::endl;
      std::cout << "\t" << this->_detection_model << std::endl;
      for (auto model : this->_classification_models) {
	std::cout << "Classification Model:\t" <<  model.name;
	std::cout << "\t" << model << std::endl;
      }
      std::cout << "CaptureSource:\n\t" <<this->_source << std::endl << std::endl;
      std::cout << header << std::endl << std::endl;
    }

    void run() {
      this->run<0>();
    }
    
    template<unsigned int N>
    void run() {
      Avg avg;
      std::size_t frames = 0u;            // Frame counter (not produced by the graph)
      std::ofstream fout(this->_destination,
			 std::ios::out);
      auto source = cv::gapi::wip::make_src<cv::gapi::wip::GCaptureSource>(this->_source);
      this->_pipeline.setSource(source);
      avg.start();
      this->_pipeline.start();
      std::vector<postproc::ObjectDetectionResult> objects;
      std::vector<cv::Rect> regions;
      std::array<std::vector<cv::Mat>,N> attributes;
      

      auto out_vector = cv::gout(objects,regions);

      for (int i = 0; i <N; i++) {
	out_vector.push_back(cv::GRunArgP(cv::detail::VectorRef(attributes[i])));
      }
      
      while(this->_pipeline.running()) {
	if (!this->_pipeline.pull(std::move(out_vector))) {
	  break;
	}
	fout << objects_to_json<N>(objects, attributes, frames) << '\n';
	fout.flush();
	if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_VERBOSE) {
	  std::cout << objects_to_json<N>(objects, attributes, frames) << std::endl;  
	}
	frames++;
	if (frames % 50 == 0) {
	  if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_INFO) {
	    std::cout << "frames: " << frames << " fps: " << avg.fps(frames) << std::endl;
	  }
	}
	
      }
      if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_INFO) {
	std::cout << "frames: " << frames << " fps: " << avg.fps(frames) << std::endl;
      }
    }

  };

  class ObjectClassification : public ObjectDetection {

  protected:

    void run() {
      this->ObjectDetection::run<3>();
    }

    
    virtual cv::GComputation graph(){

      cv::GComputation graph([]() {
			       // Declare an empty GMat - the beginning of the pipeline.
			       cv::GMat in;
			       
			       // Run object detection on the input frame. Result is a single GMat,
			       // internally representing an 1x1x200x7 SSD output.
			       // This is a single-patch version of infer:
			       // - Inference is running on the whole input image;
			       // - Image is converted and resized to the network's expected format
			       //   automatically.
			       cv::GMat detections = cv::gapi::infer<modelutil::Detections>(in);
			       
			       // Parse SSD output to a list of ROI (rectangles) using
			       // a custom kernel. Note: parsing SSD may become a "standard" kernel.
			       
			       cv::GArray<cv::Rect> regions;
			       cv::GArray<postproc::ObjectDetectionResult> objects;
			       
			       objects = postproc::SSDPostProc::on(detections,in);
			       regions = postproc::ExtractRegions::on(objects);

			       cv::GArray<cv::GMat> classifications = cv::gapi::infer<modelutil::Classifications>(regions, in);

			       cv::GArray<cv::GMat> classifications_two_layer_0;
			       cv::GArray<cv::GMat> classifications_two_layer_1;
			       
			       std::tie(classifications_two_layer_0, classifications_two_layer_1) =
				 cv::gapi::infer<modelutil::ClassificationsTwoLayers>(regions, in);			       
			       
			       // Now specify the computation's boundaries - our pipeline consumes
			       // one images and produces five outputs.
			       return cv::GComputation(cv::GIn(in),
						       cv::GOut(objects,
								regions,
								classifications,
								classifications_two_layer_0,
								classifications_two_layer_1));
			       
			     });
	return graph;
    }

    
  public:
    ObjectClassification(YAML::Node &config):ObjectDetection(config,"detection-model")
    {}


  };

  
  std::unique_ptr<Task> Task::Create(YAML::Node &config)
  {
    if (config["pipeline"]["task"].as<std::string>()=="object-detection") {
      return std::unique_ptr<ObjectDetection>(new ObjectDetection(config));
    }else if (config["pipeline"]["task"].as<std::string>()=="object-classification") {
      return std::unique_ptr<ObjectClassification>(new ObjectClassification(config));
    }
    else {
      return NULL;
    }
    
  }

}
