#pragma once
#include "yaml-cpp/yaml.h"
#include <nlohmann/json.hpp>
#include <memory>
#include "opencv2/core/utils/filesystem.hpp"
#include "postproc.hpp"
#include <fstream>
#include <opencv2/gapi/imgproc.hpp>
#include "opencv2/core/utils/logger.hpp"

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

  struct ModelIR {
    std::string xml;
    std::string bin;
    ModelIR(std::string _xml, std::string _bin):xml(_xml),bin(_bin)
    {}
    ModelIR() = default;
  };

  
  struct ModelParameters
  {
    json proc;
    std::string proc_path;
    std::map<std::string,ModelIR> precisions;
  };

  std::ostream&operator<<(std::ostream&strm, const ModelParameters&item) {

    strm << item.proc_path << std::endl;

    for (auto precision : item.precisions) {
      strm << precision.first << std::endl;
      strm << '\t' << precision.second.xml << std::endl;
      strm << '\t' << precision.second.bin << std::endl;
    }
    
    return strm;
  }
    

  inline bool ends_with(std::string const & value, std::string const & ending)
  {
    if (ending.size() > value.size()) return false;
    return std::equal(ending.rbegin(), ending.rend(), value.rbegin());
  }

  void find_model_ir(std::string models_root,
		     const std::string &model_name,
		     std::map<std::string,ModelIR> &result) {
    auto xml_candidate = model_name + ".xml";
    result.clear();
    std::vector<cv::String> xml_candidates;
    cv::utils::fs::glob_relative(cv::utils::fs::join(models_root,
						     model_name),
				 "*.xml",
				 xml_candidates,
				 true);
    
    for (auto candidate : xml_candidates) {
      if (ends_with(candidate, xml_candidate)) {
	auto precision = cv::utils::fs::getParent(candidate);
	auto bin_candidate(candidate);
	bin_candidate.replace(candidate.length()-strlen("xml"),
			      3,
			      "bin");
	auto full_xml_path = cv::utils::fs::join(cv::utils::fs::join(models_root,model_name),
						 candidate);
	auto full_bin_path = cv::utils::fs::join(cv::utils::fs::join(models_root,model_name),
						 bin_candidate);
			
	
	if (cv::utils::fs::exists(full_xml_path) && cv::utils::fs::exists(full_bin_path))
	  {
	    result.emplace(precision,ModelIR(full_xml_path,
					     full_bin_path));
	    
	  }
      }
    }
  }
  
  std::string find_model_proc(std::string models_root,
			      const std::string &model_name) {
    std::string result = "";    

    auto candidate = model_name + ".json";

    std::vector<cv::String> proc_candidates;

    cv::utils::fs::glob(cv::utils::fs::join(models_root,
					    model_name),
			"*.json",
			proc_candidates,
			true);
    for (auto proc_candidate : proc_candidates) {
      if (ends_with(proc_candidate,candidate)) {
	result = proc_candidate;
	break;
      }
    }
    if ((result == "") && (!proc_candidates.empty())) {
      result = proc_candidates[0];
    }
    return result;
  }
  
  
  ModelParameters &find_model(YAML::Node &config,
			      const std::string &model_name,
			      ModelParameters &mp) {

    std::string models_root = config["runner-config"]["models_root"].as<std::string>();

    mp.proc_path = find_model_proc(models_root,model_name);

    if (mp.proc_path != "") {
      std::ifstream input(mp.proc_path);    
      input >> mp.proc;
    } else {
      mp.proc["output_postproc"][0]["converter"] = "tensor_to_bbox_ssd";
    }
    
    find_model_ir(models_root, model_name, mp.precisions);
    return mp;
  }
  
  struct Task
  {
    virtual ~Task() = default;
    static std::unique_ptr<Task> Create(YAML::Node &config);
    virtual void run() = 0;
    virtual void log_details() = 0;
  };
  
  class ObjectDetection: public Task {
    
  private:
    
    YAML::Node &_config;
    ModelParameters _model;
    cv::GStreamingCompiled _pipeline;

    // object detector: takes one Mat, returns another Mat
    G_API_NET(Detections, <cv::GMat(cv::GMat)>, "object-detector");


    std::string _source;
    std::string _destination;
    int _frame_height;
    int _frame_width;
    uint64_t _frame_duration_ns;
    std::string _source_path;
  public:

        
    ObjectDetection(YAML::Node &config, const std::string& detect_model_config="model"):_config(config),
										_source(this->_create_source_string()),
										_destination(this->_create_destination_string()),
										_source_path(this->_get_source_path()) {
      find_model(config,
		 config["pipeline"][detect_model_config].as<std::string>(),
		 this->_model);

      auto converter = this->_model.proc["output_postproc"][0]["converter"];
      
      if ( converter != "tensor_to_bbox_ssd" ) {
	std::cout << "Post Proc" << converter << "Not Supported" << "\n";
	throw "unsupported";
      }
      
      cv::GComputation graph([]() {
			    // Declare an empty GMat - the beginning of the pipeline.
			    cv::GMat in;
			    
			    // Run object detection on the input frame. Result is a single GMat,
			    // internally representing an 1x1x200x7 SSD output.
			    // This is a single-patch version of infer:
			    // - Inference is running on the whole input image;
			    // - Image is converted and resized to the network's expected format
			    //   automatically.
			    cv::GMat detections = cv::gapi::infer<Detections>(in);

			    // Parse SSD output to a list of ROI (rectangles) using
			    // a custom kernel. Note: parsing SSD may become a "standard" kernel.
			    cv::GArray<postproc::ObjectDetectionResult> objects =
			      postproc::SSDPostProc::on(detections, in);

			    // Now specify the computation's boundaries - our pipeline consumes
			    // one images and produces five outputs.
			    return cv::GComputation(cv::GIn(in),
						    cv::GOut(objects));

			  });

      
      auto runner_config = this->_config["runner-config"];
      
      this->set_default(runner_config,
			"detect",YAML::Node());

      this->set_default(runner_config["detect"],
			"device",
			"CPU");
      
      auto device = runner_config["detect"]["device"].as<std::string>();

      std::map<const std::string, const std::string> device_map = { {"CPU","FP32"},
								    {"GPU","FP16"}};
      auto precision = device_map[device];
      
      auto det_net = cv::gapi::ie::Params<Detections> {
						       this->_model.precisions[precision].xml,   
						       this->_model.precisions[precision].bin,   
						       device,   
      };

      auto kernels = cv::gapi::kernels<postproc::OCVSSDPostProc>();
      auto networks = cv::gapi::networks(det_net);
      
      this->_pipeline = graph.compileStreaming(cv::compile_args(kernels, networks));

    }

    template<class T>
    void set_default(YAML::Node node,
		     const std::string &key,
		     T value) {
      if (!node[key]) {
	node[key] = value;
      }
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
      
      this->set_default(config,
			"decode",YAML::Node());

      this->set_default(config["decode"],
			"device",
			"CPU");

      auto device = config["decode"]["device"].as<std::string>();
      
      std::map<const std::string, const std::string> device_map = { {"CPU","decodebin"},
								    {"GPU","vaapidecodebin"}};
      auto media_type_iterator = media_type_map.find(media_type);
      if (media_type_iterator != media_type_map.end()) {
        device_map = media_type_iterator->second;
      }

      this->set_default(config["decode"],
			"element",
			device_map[device]);
      
      if (config["decode"]["element"].as<std::string>()=="avdec_h264") {
	this->set_default(config["decode"],"max-threads","1");
      }

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
      result << "videoconvert n-threads=" << cv::getNumThreads();
      return result.str();
    }
    
    std::string _create_appsink() {
      std::ostringstream result;
      result << "appsink sync=false emit-signals=false max-buffers=1";
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
      this->set_default(this->_config["inputs"][0],
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

    json objects_to_json(const std::vector<postproc::ObjectDetectionResult> &objects,
			 int frame_index) {
      json result;
      result["resolution"] = { {"height", this->_frame_height},
			       {"width", this->_frame_width} };

      result["timestamp"] = frame_index * this->_frame_duration_ns;
      result["source"] = this->_source_path;

      for (auto object : objects) {
	auto label = this->_model.proc["output_postproc"][0]["labels"][int(object.object_type)];

	json detection = { {"bounding_box", {"x_max",object.roi_right,
					     "x_min",object.roi_left,
					     "y_min",object.roi_top,
					     "y_max",object.roi_bottom}},
			   {"confidence",object.confidence},
			   {"label",label},
			   {"label_id",object.object_type}};
	
	
	result["objects"].push_back( { {"detection", detection},
				       {"h", object.roi.height},
				       {"w", object.roi.width},
				       {"x", object.roi.x},
				       {"y", object.roi.y} } );
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
      std::cout << "Model:\t" <<this->_config["pipeline"]["model"] << std::endl << std::endl;
      std::cout << "\t" << this->_model << std::endl;
      std::cout << "CaptureSource:\n\t" <<this->_source << std::endl << std::endl;
      std::cout << header << std::endl << std::endl;
    }
    
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
      auto out_vector = cv::gout(objects);
      while(this->_pipeline.running()) {
	if (!this->_pipeline.pull(std::move(out_vector))) {
	  break;
	}
	fout << objects_to_json(objects, frames) << '\n';
	fout.flush();
	if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_VERBOSE) {
	  std::cout << objects_to_json(objects, frames) << std::endl;
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
