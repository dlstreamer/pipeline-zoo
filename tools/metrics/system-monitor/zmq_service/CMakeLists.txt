cmake_minimum_required(VERSION 3.1)

set (TARGET_NAME "sys_monitor_service")
set (CMAKE_CXX_STANDARD 11)

find_package(PkgConfig)
include(FindPkgConfig)
pkg_check_modules(PC_ZEROMQ REQUIRED "libzmq")

set(MAIN_SRC
        zmq_service.cpp
        )

set(MAIN_HEADERS
        )

add_executable(${TARGET_NAME} ${MAIN_SRC} ${MAIN_HEADERS})

target_link_libraries(${TARGET_NAME} zmq core igt)


# Install binary
install(TARGETS ${TARGET_NAME} DESTINATION bin)
