# ===========================================================================
# CMAKE PART: BUILD_CONFIG="{OS}_{PROCESSOR}_{CMAKE_BUILD_TYPE}"
# ===========================================================================
# USE: include("${PROJECT_SOURCE_DIR}/../cmake/build_config.cmake")

include_guard(DIRECTORY)

if("${BUILD_CONFIG_TYPE}" STREQUAL "")
    set(BUILD_CONFIG_TYPE "debug")
endif()
string(TOLOWER "${BUILD_CONFIG_TYPE}" BUILD_CONFIG_TYPE)

set(BUILD_CONFIG_OS     "${CMAKE_HOST_SYSTEM_NAME}")
set(BUILD_CONFIG_ARCH   "${CMAKE_HOST_SYSTEM_PROCESSOR}")
if("${BUILD_CONFIG}" STREQUAL "")
    set(BUILD_CONFIG "${BUILD_CONFIG_OS}_${BUILD_CONFIG_ARCH}_${BUILD_CONFIG_TYPE}")
endif()
message(STATUS "BUILD_CONFIG=${BUILD_CONFIG}")
