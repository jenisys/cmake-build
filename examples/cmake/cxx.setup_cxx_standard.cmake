# ===========================================================================
# CMAKE C++ COMPILER SETUP: cmake/cxx.setup_cxx_standard.cmake
# ===========================================================================
# HINTS: 
#   * CMAKE_CXX_STANDARD: Needs to defined before target to have any effect.
#
# OPTIONAL FILES:
#   ${PROJECT_SOURCE_DIR}/.cmake_project.cxx_standard
#       CMake include file to specify the C++ standard for this project.
#
# FILE EXAMPLE:
#   # -- FILE: .cmake_project.cxx_standard
#   set(CMAKE_CXX_STANDARD 17)
#   set(CMAKE_CXX_STANDARD_REQUIRED ON)
#   set(CMAKE_CXX_EXTENSIONS OFF)
# ===========================================================================

include("${PROJECT_SOURCE_DIR}/.cmake_project.cxx_standard" OPTIONAL)
if(NOT DEFINED CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)  # Enable C++14 standard
endif()
if(NOT DEFINED CMAKE_CXX_STANDARD_REQUIRED)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()
if(NOT DEFINED CMAKE_CXX_EXTENSIONS)
    set(CMAKE_CXX_EXTENSIONS OFF)
endif()

# -- OLD:
# set(PROJECT_CMAKE_CXX_STANDARD_FILE "${PROJECT_SOURCE_DIR}/.cmake_project.cxx_standard")
# if(EXISTS "${PROJECT_CMAKE_CXX_STANDARD_FILE}")
#    file(READ "${PROJECT_CMAKE_CXX_STANDARD_FILE}" CMAKE_CXX_STANDARD)
#    string(STRIP "${CMAKE_CXX_STANDARD}" CMAKE_CXX_STANDARD)
# endif()
message(STATUS "USING: CMAKE_CXX_STANDARD=${CMAKE_CXX_STANDARD} (REQUIRED: ${CMAKE_CXX_STANDARD_REQUIRED}, EXTENSIONS: ${CMAKE_CXX_EXTENSIONS})")
