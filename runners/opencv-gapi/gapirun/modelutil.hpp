#pragma once
#include "yaml-cpp/yaml.h"
#include <nlohmann/json.hpp>

using json = nlohmann::json;

namespace modelutil {

  inline bool starts_with(std::string const & value, std::string const & beginning)
  {
    if (beginning.size() > value.size()) return false;
    return std::equal(beginning.begin(), beginning.end(), value.begin());
  }

  
  inline bool ends_with(std::string const & value, std::string const & ending)
  {
    if (ending.size() > value.size()) return false;
    return std::equal(ending.rbegin(), ending.rend(), value.rbegin());
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
    static std::map<const std::string, const std::string> device_to_precision; 
    json proc;
    std::string proc_path;
    std::map<std::string,ModelIR> precisions;
    std::string name;

    template<class T>
    cv::gapi::ie::Params<T>params(std::string const &device,
				  std::string const &precision) {
      
      auto default_precision = starts_with(device,"MULTI") ? device_to_precision["MULTI"] : device_to_precision[device];

      if (precision == "") {
	return cv::gapi::ie::Params<T> {
	  this->precisions[default_precision].xml,   
	    this->precisions[default_precision].bin,   
	    device   
	    };
      } else {
	return cv::gapi::ie::Params<T> {
	  this->precisions[precision].xml,   
	    this->precisions[precision].bin,   
	    device   
	    };
      }
    }
  };
    
  std::map<const std::string, const std::string> ModelParameters::device_to_precision= { {"CPU","FP32"},
											 {"GPU","FP16"},
											 {"HDDL","FP16"},
											 {"MULTI","FP16"} };

  
  std::ostream&operator<<(std::ostream&strm, const ModelParameters&item) {
    
    strm << item.proc_path << std::endl;
    
    for (auto precision : item.precisions) {
      strm << precision.first << std::endl;
      strm << '\t' << precision.second.xml << std::endl;
      strm << '\t' << precision.second.bin << std::endl;
    }
    
    return strm;
  }

  
  void find_model_ir(std::string models_root,
		     const std::string &model_name,
		     std::map<std::string,ModelIR> &result,
		     bool clear=true) {
    auto xml_candidate = model_name + ".xml";
    if (clear) {
      result.clear();
    }
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
    auto int8_model = model_name+"_INT8";
    auto int8_model_candidate = cv::utils::fs::join(models_root,int8_model);
    
    if (cv::utils::fs::exists(int8_model_candidate)) {
      find_model_ir(models_root,int8_model,result,false);
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

    std::string models_root = config["models-root"].as<std::string>();
    
    mp.proc_path = find_model_proc(models_root,model_name);
    mp.name = model_name;
    if (mp.proc_path != "") {
      std::ifstream input(mp.proc_path);    
      input >> mp.proc;
    } else {
      mp.proc["output_postproc"][0]["converter"] = "tensor_to_bbox_ssd";
    }
    find_model_ir(models_root, model_name, mp.precisions);
    return mp;
  }

  // object detector: takes one Mat, returns another Mat
  G_API_NET(Detections, <cv::GMat(cv::GMat)>, "object-detector");

  // object classifier: takes one Mat, returns another Mat
  G_API_NET(Classifications, <cv::GMat(cv::GMat)>, "object-classifier");
  
    // object classifier: takes one Mat, returns 2 Mats
  using ClassifierOutputTwoLayers = std::tuple<cv::GMat, cv::GMat>; 
  G_API_NET(ClassificationsTwoLayers, <ClassifierOutputTwoLayers(cv::GMat)>, "object-classifier-two-layers");

 
}
