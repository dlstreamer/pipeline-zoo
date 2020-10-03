cmake_minimum_required(VERSION 3.1)

set(TARGET_NAME "core")
project(${TARGET_NAME} C)

find_package(PkgConfig REQUIRED)
pkg_check_modules(PKG_PAPI REQUIRED papi)

if(NOT DEFINED CMAKE_INSTALL_LIBDIR)
    set(CMAKE_INSTALL_LIBDIR "lib")
endif()

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(CORE_SOURCES
        src/procstatreader.c
        src/cpustat.c
        src/gpustat.c
        src/pwrstat.c
        src/utils.c
        src/sm.c
        )

set(CORE_HEADERS
        include/procstatreader.h
        include/cpustat.h
        include/gpustat.h
        include/pwrstat.h
        include/utils.h
        include/sm.h
        )

add_library(${TARGET_NAME} SHARED ${CORE_HEADERS} ${CORE_SOURCES})
target_link_libraries(${TARGET_NAME} PRIVATE igt papi)

target_include_directories(${TARGET_NAME}
PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
PRIVATE
        ${PKG_PAPI_INCLUDE_DIRS}
        )

install(TARGETS ${TARGET_NAME} DESTINATION "${CMAKE_INSTALL_LIBDIR}")