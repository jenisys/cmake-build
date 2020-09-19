# ===========================================================================
# CMAKE SETUP C++ PROJECT: cmake/cxx.setup_project.cmake
# ===========================================================================
# STATE:  beta
# DESCRIPTION:
#   Provides basic setup for C++ project (common parts)
#   before any targets (like: add_executable(), add_library(), ...)
#   are defined.
#
#   * Setup CMAKE_BUILD_TYPE if undefined
#   * Setup default C/C++ compile-definions based on CMAKE_BUILD_TYPE
#   * Setup CMAKE_CXX_STANDARD, ... undefined
#   * Setup directory-layout (bin/, lib/ directories) in CMAKE_BUILD_DIRECTORY
#
# REQUIRES: INCLUDE BEFORE ANY-TARGET (add_executable(), add_library(), ...)
# DEPENDS ON:
#   * cxx.setup_cxx_standard.cmake
#   * build_config
# ===========================================================================

include_guard(DIRECTORY)

# -- CMAKE_CONFIGURATION_TYPES
if(NOT DEFINED CMAKE_BUILD_TYPE)
    SET(CMAKE_BUILD_TYPE "Release" CACHE STRING "CMake build type: Debug, Release, ...")
endif()
# SET(CMAKE_CONFIGURATION_TYPES "Debug;Release" CACHE STRING "Configs" FORCE)
# IF(DEFINED CMAKE_BUILD_TYPE AND CMAKE_VERSION VERSION_GREATER "2.8")
#    SET_PROPERTY(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS  ${CMAKE_CONFIGURATION_TYPES})
# ENDIF()
message(STATUS "USING: CMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}")

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_definitions(DEBUG=1)
else()
    add_compile_definitions(NDEBUG=1)
endif()

# -- ARTIFACT DIRECTORY LAYOUT in BINARY_DIR:
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/bin")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/lib")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/lib")

# ----------------------------------------------------------------------------
# MORE C++ SETUPS:
# ----------------------------------------------------------------------------
include(cxx.setup_cxx_standard)
include(build_config)
