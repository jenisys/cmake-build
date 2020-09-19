# ===========================================================================
# CMAKE C++ COMPILER SETUP: cmake/cxx.setup_cxx_standard.cmake
# ===========================================================================
# HINTS:
#   * CMAKE_CXX_STANDARD: Needs to defined before any target
#     (add_executable(), add_library(), ...)
#   * CMAKE_CXX_STANDARD: Should be defined before this file is included.
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
#
# SEE ALSO:
#   * https://cmake.org/cmake/help/v3.16/variable/CMAKE_CXX_STANDARD.html
# ===========================================================================

include_guard(DIRECTORY)

# -- OPTIONAL: Provide own project-specific C++ compiler setup file.
# SUPPORT OVERRIDE: As -DCMAKE_CXX_STANDARD=... on command-line (or "CMakeLists.txt" file).
if(NOT DEFINED CMAKE_CXX_STANDARD)
    include("${PROJECT_SOURCE_DIR}/.cmake_project.cxx_standard" OPTIONAL)
endif()

# ---------------------------------------------------------------------------
# SANE DEFAULTS: If ".cmake_project.cxx_standard" is missing
# ---------------------------------------------------------------------------
if(NOT DEFINED CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)  # Enable C++17 standard
endif()
if(NOT DEFINED CMAKE_CXX_STANDARD_REQUIRED)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
endif()
if(NOT DEFINED CMAKE_CXX_EXTENSIONS)
    set(CMAKE_CXX_EXTENSIONS OFF)
endif()

# ---------------------------------------------------------------------------
# SHOW CONFIG RESULT:
# ---------------------------------------------------------------------------
message(STATUS "USING: CMAKE_CXX_COMPILER_ID=${CMAKE_CXX_COMPILER_ID}")
message(STATUS "USING: CMAKE_CXX_STANDARD=${CMAKE_CXX_STANDARD} (REQUIRED: ${CMAKE_CXX_STANDARD_REQUIRED}, EXTENSIONS: ${CMAKE_CXX_EXTENSIONS})")
