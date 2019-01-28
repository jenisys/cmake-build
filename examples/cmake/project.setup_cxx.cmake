# ===========================================================================
# PROJECT-SPECIFIC CMAKE SCRIPT: Setup C++ Builds
# ===========================================================================
# REQUIRE-INCLUDE: Before any target is defined, like: add_library(), ...

set(TOPDIR "${CMAKE_CURRENT_SOURCE_DIR}/..")

# ---------------------------------------------------------------------------
# SECTION: C++ Compiler Specification and Requirements
# ---------------------------------------------------------------------------
# -- CMAKE_CXX_STANDARD: Needs to defined before target to have any effect.
set(CMAKE_CXX_STANDARD 14)  # Enable C++14 standard

set(CMAKE_CXX_EXTRA_FLAGS "-Wall -Wpedantic")
# include("${PROJECT_SOURCE_DIR}/../cmake/build_config.cmake")
