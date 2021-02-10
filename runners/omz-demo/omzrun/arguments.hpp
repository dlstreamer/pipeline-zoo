#pragma once
#include "opencv2/core/utils/logger.hpp"

namespace cmdline {
  const std::string about =
    "This is an Open Model Zoo Demo Pipeline Runner";
  const std::string arguments =
    "{ h help | | print this help message }"
    "{ s systeminfo | | system information }"
    "{ l log-level | | log level (silent,fatal,error,warning,info,debug,verbose)}"
    "{ @piperun_config | | piperun configuration file (.piperun.yml)}";

  cv::CommandLineParser parse_args(int argc, char *argv[]) {
    cv::CommandLineParser args(argc, argv, arguments);
    
    args.about(about);
    if (args.has("help")) {
        args.printMessage();
	std::exit(0);
    }

    if (!args.check())
    {
        args.printErrors();
	std::exit(1);
    }

    if (!args.has("@piperun_config")) {
      std::cout << "\n\nPiperun configuration is required." << "\n\n";
      args.printMessage();
      std::exit(1);
    }
    return args;
  }

  cv::utils::logging::LogLevel parse_log_level(std::string log_level) {
    static std::map<std::string, cv::utils::logging::LogLevel> log_level_map= { {"silent", cv::utils::logging::LogLevel::LOG_LEVEL_SILENT},
										{"fatal", cv::utils::logging::LogLevel::LOG_LEVEL_FATAL},
										{"error", cv::utils::logging::LogLevel::LOG_LEVEL_ERROR},
										{"warning", cv::utils::logging::LogLevel::LOG_LEVEL_WARNING},
										{"info", cv::utils::logging::LogLevel::LOG_LEVEL_INFO},
										{"debug", cv::utils::logging::LogLevel::LOG_LEVEL_DEBUG},
										{"verbose", cv::utils::logging::LogLevel::LOG_LEVEL_VERBOSE}};
    
    return log_level_map[log_level];
  }
  
}

