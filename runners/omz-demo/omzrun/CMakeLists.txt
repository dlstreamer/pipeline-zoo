cmake_minimum_required(VERSION 2.8)
project(omzrun)
find_package(OpenCV REQUIRED)
find_package(yaml-cpp REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(InferenceEngine 2.0 REQUIRED)
find_package(ngraph REQUIRED)

include_directories( ${OpenCV_INCLUDE_DIRS} ${YAML_CPP_INCLUDE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_src/demos/common/include ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_src/demos/common/models/include ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_src/demos/common/monitors/include ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_src/demos/common/pipelines/include ${InferenceEngine_INCLUDE} ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_build/thirdparty/gflags/include )

add_executable(omzrun main.cpp)

target_link_libraries( omzrun ${OpenCV_LIBS} ${YAML_CPP_LIBRARIES} ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_build/intel64/Release/lib/libgflags_nothreads.a ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_build/intel64/Release/lib/libmonitors.a ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_build/intel64/Release/lib/libmodels.a ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_build/intel64/Release/lib/libpipelines.a ${InferenceEngine_LIBRARIES} ngraph::ngraph  ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_build/intel64/Release/lib/libcommon.a ${CMAKE_CURRENT_SOURCE_DIR}/../omz_demos_build/intel64/Release/lib/libgflags_nothreads.a ${OpenCV_LIBS})
