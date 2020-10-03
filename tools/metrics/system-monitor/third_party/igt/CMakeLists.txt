cmake_minimum_required(VERSION 3.1)

set(TARGET_NAME "igt")
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

project(${TARGET_NAME})

set(IGT_SOURCES
        src/igt_perf.c
        )

set(IGT_HEADERS
        include/igt_core.h
        include/igt_debugfs.h
        include/igt_dummyload.h
        include/igt_gt.h
        include/igt_list.h
        include/igt_perf.h

        include/drm_uapi/drm.h
        include/drm_uapi/drm_mode.h
        include/drm_uapi/i915_drm.h
        )

source_group("src" FILES ${IGT_SOURCES})
source_group("include" FILES ${IGT_HEADERS})

add_library(${TARGET_NAME} STATIC ${IGT_HEADERS} ${IGT_SOURCES})
target_include_directories(${TARGET_NAME}
PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/include/drm_uapi
        )
