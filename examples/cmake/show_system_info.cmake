# ===========================================================================
# CMAKE PART: BUILD_CONFIG="{OS}_{PROCESSOR}_{CMAKE_BUILD_TYPE}"
# ===========================================================================
# USE: include("${PROJECT_SOURCE_DIR}/../cmake/show_system_info.cmake")

cmake_host_system_information(RESULT HOSTNAME QUERY HOSTNAME)
cmake_host_system_information(RESULT ARCH_PROCESSOR  QUERY PROCESSOR_NAME)

cmake_host_system_information(RESULT ARCH_OS_NAME    QUERY OS_NAME)
# SEE: CMAKE_HOST_SYSTEM_NAME
cmake_host_system_information(RESULT ARCH_OS_RELEASE QUERY OS_RELEASE)
cmake_host_system_information(RESULT ARCH_OS_VERSION QUERY OS_VERSION)
cmake_host_system_information(RESULT ARCH_OS_PLATFORM QUERY OS_PLATFORM)
# SEE: CMAKE_HOST_SYSTEM_PROCESSOR

message(STATUS "HOSTNAME       = ${HOSTNAME}")
message(STATUS "PROCESSOR_NAME = ${ARCH_PROCESSOR}")
message(STATUS "OS_NAME        = ${ARCH_OS_NAME}")
message(STATUS "OS_RELEASE     = ${ARCH_OS_RELEASE}")
message(STATUS "OS_VERSION     = ${ARCH_OS_VERSION}")
message(STATUS "OS_PLATFORM    = ${ARCH_OS_PLATFORM}")
message(STATUS "CMAKE_HOST_SYSTEM_NAME       = ${CMAKE_HOST_SYSTEM_NAME}")
message(STATUS "CMAKE_HOST_SYSTEM_PROCESSOR  = ${CMAKE_HOST_SYSTEM_PROCESSOR}")
