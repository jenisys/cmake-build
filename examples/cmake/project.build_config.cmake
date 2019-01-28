# ===========================================================================
# CMAKE PART: BUILD_CONFIG="{OS}_{PROCESSOR}_{CMAKE_BUILD_TYPE}"
# ===========================================================================
# USE: include("${PROJECT_SOURCE_DIR}/../cmake/build_config.cmake")

include_guard(DIRECTORY)

if("${CMAKE_BUILD_TYPE}" STREQUAL "")
    set(CMAKE_BUILD_TYPE "Debug")
endif()
if("${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "")
    set(CMAKE_SYSTEM_PROCESSOR "${CMAKE_HOST_SYSTEM_PROCESSOR}")
endif()


string(TOLOWER "${CMAKE_BUILD_TYPE}"  BUILD_CONFIG_TYPE)
string(TOLOWER "${CMAKE_SYSTEM_NAME}" BUILD_CONFIG_OS)
set(BUILD_CONFIG_ARCH   "${CMAKE_SYSTEM_PROCESSOR}")
# set(BUILD_CONFIG_TYPE "${CMAKE_BUILD_TYPE}")
# set(BUILD_CONFIG_OS   "${CMAKE_SYSTEM_NAME}")
string(TOLOWER "${BUILD_CONFIG_TYPE}"  BUILD_CONFIG_TYPE)

if("${BUILD_CONFIG}" STREQUAL "")
    set(BUILD_CONFIG "${BUILD_CONFIG_OS}_${BUILD_CONFIG_ARCH}_${BUILD_CONFIG_TYPE}")
endif()
message(STATUS "BUILD_CONFIG=${BUILD_CONFIG}")
