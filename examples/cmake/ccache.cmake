cmake_minimum_required(VERSION 3.4)
# ===========================================================================
# CMAKE TOOLCHAIN: ccache.cmake
# ===========================================================================
# REQUIRES: CMake >= 3.4
# SUPPORTS: cmake.generator=ninja, make
# DESCRIPTION:
#   Uses ccache, as compiler build-time optimzer, if available.
#   Otherwise, the native compiler toolchain is used.
#
# CMAKE-USAGE: Requires include-before-project-statement
#   # -- FILE: CMakeLists.txt
#   cmake_minimum_required(VERSION 3.4)
#   include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/ccache.cmake)
#   project(...)
#
# USAGE:
#   ccache --clear
#   ccache --cleanup
#   ccache --show-stats
#   ccache --zero-stats
#
# SEE ALSO:
#   * https://ccache.dev/
#   * https://ccache.dev/manual/latest.html
#   * https://crascit.com/2016/04/09/using-ccache-with-cmake/
# ===========================================================================
# ALTERNATIVE SOLUTION (requires: CMake >= 3.4):
#   cmake -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
#
# ===========================================================================
# CCACHE_DIR : path = Where ccache compiled output is kept; $HOME/.ccache
include_guard(DIRECTORY)

option(USE_CCACHE "Enable/Disable CCACHE (Compiler Cache) usage" ON)
find_program(CCACHE_PROGRAM ccache)

if(CCACHE_PROGRAM)
    if(USE_CCACHE)
        message(STATUS "USING: ccache (found: ${CCACHE_PROGRAM})")
        set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${CCACHE_PROGRAM}")
        set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK    "${CCACHE_PROGRAM}")
    else()
        message(STATUS "DISABLED: ccache (found: ${CCACHE_PROGRAM}; USE_CCACHE=yes to enable)")
    endif()
endif()
