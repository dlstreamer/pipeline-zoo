cmake_minimum_required (VERSION 3.1)

project(system_monitor)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O0 -ggdb")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O0 -ggdb")

add_subdirectory(core_lib)
add_subdirectory(cmd_client)
add_subdirectory(third_party)
#add_subdirectory(zmq_service)