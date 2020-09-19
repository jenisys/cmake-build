# ===========================================================================
# CMAKE PART: BUILD_CONFIG="{OS}_{PROCESSOR}_{CMAKE_BUILD_TYPE}"
# ===========================================================================
# USE: include("${PROJECT_SOURCE_DIR}/cmake/build_config.cmake")

include_guard(DIRECTORY)

if(NOT DEFINED CMAKE_BUILD_TYPE)
    SET(CMAKE_BUILD_TYPE "Release" CACHE STRING "CMake build type" FORCE)
endif()
set(BUILD_CONFIG_TYPE "${CMAKE_BUILD_TYPE}")
string(TOLOWER "${BUILD_CONFIG_TYPE}" BUILD_CONFIG_TYPE)
# DISABLED: set(CMAKE_BUILD_TYPE ${BUILD_CONFIG_TYPE})

set(BUILD_CONFIG_OS     "${CMAKE_SYSTEM_NAME}")
set(BUILD_CONFIG_ARCH   "${CMAKE_SYSTEM_PROCESSOR}")
if("${BUILD_CONFIG}" STREQUAL "")
    set(BUILD_CONFIG "${BUILD_CONFIG_OS}_${BUILD_CONFIG_ARCH}_${BUILD_CONFIG_TYPE}")
endif()
message(STATUS "USING: BUILD_CONFIG=${BUILD_CONFIG}")
