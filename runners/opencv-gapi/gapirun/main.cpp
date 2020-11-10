#include "opencv2/opencv_modules.hpp"
#if defined(HAVE_OPENCV_GAPI)

#include <chrono>
#include <iomanip>

#include "opencv2/imgproc.hpp"
#include "opencv2/highgui.hpp"
#include "opencv2/core/utils/logger.hpp"
#include "opencv2/gapi.hpp"
#include "opencv2/gapi/core.hpp"
#include "opencv2/gapi/imgproc.hpp"
#include "opencv2/gapi/infer.hpp"
#include "opencv2/gapi/infer/ie.hpp"
#include "opencv2/gapi/cpu/gcpukernel.hpp"
#include "opencv2/gapi/streaming/cap.hpp"
#include "yaml-cpp/yaml.h"
#include "arguments.hpp"
#include "task.hpp"

int main(int argc, char *argv[])
{
  cv::CommandLineParser args=cmdline::parse_args(argc, argv);

  YAML::Node config;

  try {
    std::cout << args.get<cv::String>("@piperun_config") <<'\n';
    config= YAML::LoadFile(args.get<cv::String>("@piperun_config"));
  } catch (...) {
    std::cout << "Invalid or Missing Configuration File: " << args.get<cv::String>("@piperun_config") <<"\n";
    exit(1);
  }

  if (args.has("log-level")) {
    cv::utils::logging::setLogLevel(cmdline::parse_log_level(args.get<std::string>("log-level")));
    
  } else if (config["runner-config"]["log-level"]) {
    cv::utils::logging::setLogLevel(cmdline::parse_log_level(config["runner-config"]["log-level"].as<std::string>()));	
  } else {
    cv::utils::logging::setLogLevel(cmdline::parse_log_level("info"));	
  }
  
  
  std::unique_ptr<task::Task> task = task::Task::Create(config);
  
  if (!task) {
    std::cout << "Unsupported Task" << '\n';
    exit(1);
  }

  if (cv::utils::logging::getLogLevel() >= cv::utils::logging::LogLevel::LOG_LEVEL_INFO) {
    task->log_details();
  }

  task->init();
  task->run();
  
}
#else
#include <iostream>
int main()
{
    std::cerr << "This tutorial code requires G-API module "
                 "with Inference Engine backend to run"
              << std::endl;
    return 1;
}
#endif  // HAVE_OPECV_GAPI
