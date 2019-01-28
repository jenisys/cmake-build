# ===========================================================================
# CMAKE PART: PROJECT-SPECIFIC: Setup C++ Build Projects
# ===========================================================================
# USE: INCLUDE-BEFORE add_executable(), add_library()

include_guard(DIRECTORY)

# ----------------------------------------------------------------------------
# CMAKE SETUP:
# ----------------------------------------------------------------------------
# XXX-NOT-WORKING: file(TO_NATIVE_PATH "${CMAKE_CURRENT_LIST_DIR}/.." TOPDIR)
# XXX get_filename_component(TOPDIR "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE )
get_filename_component(TOPDIR "${CMAKE_CURRENT_LIST_DIR}" DIRECTORY CACHE)
message(STATUS "USING: TOPDIR=${TOPDIR}")

# -- SETUP: CMAKE_MODULE_PATH
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")

# ----------------------------------------------------------------------------
# CMAKE C++ COMPILER SETUP:
# ----------------------------------------------------------------------------
# -- CMAKE_CXX_STANDARD: Needs to defined before target to have any effect.
set(CMAKE_CXX_STANDARD 11)  # Enable C++11 standard
set(CMAKE_CXX_EXTRA_FLAGS "-Wall -Wpedantic")
set(CMAKE_CXX_EXTRA_FLAGS "")


# ----------------------------------------------------------------------------
# MORE GENERIC PARTS:
# ----------------------------------------------------------------------------
include("${CMAKE_CURRENT_LIST_DIR}/project.build_config.cmake")


# ----------------------------------------------------------------------------
# CMAKE PROJECT-SPECIFIC SETUP:
# ----------------------------------------------------------------------------


# -- NEEDED-FOR:
if("${CMAKE_BUILD_TYPE}" STREQUAL "Release")
    add_compile_definitions(NDEBUG=1)
else()
    add_compile_definitions(DEBUG=1)
endif()


# include_directories(XXX)
# link_directories(XXX)
