cmake_minimum_required(VERSION 3.4)
# ===========================================================================
# CMAKE TOOLCHAIN: ccache_optional.cmake
# ===========================================================================
# REQUIRES: CMake >= 3.4
# SUPPORTS: cmake.generator=ninja, make
# DESCRIPTION:
#   Uses ccache, as compiler build-time optimzer, if available.
#   Otherwise, the native compiler toolchain is used.
#
# SEE ALSO:
#   * https://ccache.dev/
#   * https://ccache.dev/manual/latest.html
#   * https://crascit.com/2016/04/09/using-ccache-with-cmake/
# ===========================================================================
# ALTERNATIVE SOLUTION (requirs: CMake >= 3.4):
#   cmake -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
#
# ===========================================================================
# CCACHE_DIR : path = Where ccache compiled output is kept; $HOME/.ccache

# find_program(CCACHE_FOUND ccache)
# if(CCACHE_FOUND)
#     message(STATUS "USE: ccache")
#     set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache)
#     set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK ccache)
# endif()

find_program(CCACHE_PROGRAM ccache)
if(CCACHE_PROGRAM)
    message(STATUS "USE: ccache (found: ${CCACHE_PROGRAM})")
    set_property(GLOBAL PROPERTY RULE_LAUNCH_COMPILE "${CCACHE_PROGRAM}")
    set_property(GLOBAL PROPERTY RULE_LAUNCH_LINK    "${CCACHE_PROGRAM}")
endif()
