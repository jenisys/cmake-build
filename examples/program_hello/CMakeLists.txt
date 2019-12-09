# ===========================================================================
# CMAKE: Build one program
# ===========================================================================

cmake_minimum_required(VERSION 3.12)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../cmake")
include("ccache")

project(hello VERSION 0.1.0 LANGUAGES CXX)

set(_TOPDIR "${PROJECT_SOURCE_DIR}/..")
include(${_TOPDIR}/cmake/project.setup_cxx.cmake)


# ---------------------------------------------------------------------------
# SECTION: Targets -- One Executable/Programm
# ---------------------------------------------------------------------------
add_subdirectory("${CMAKE_CURRENT_SOURCE_DIR}/../library_hello" hello.lib)

add_executable(hello_app
    hello_main.cpp
)
target_link_libraries(hello_app HELLO::hello)
set_property(TARGET hello_app PROPERTY EchoString "CXX-BUILD: hello_app ...")

# -- AUTO-RUN TARGET:
set(HELLO_ARGS "Alice")
set(HELLO_EXPECTED_OUTPUT "Hello Alice")
add_custom_target(run-hello ALL
    COMMAND hello_app ${HELLO_ARGS}
    DEPENDS hello_app
    COMMENT "AUTO-RUN: hello_app (EXPECTED-OUTPUT: ${HELLO_EXPECTED_OUTPUT})")

# ---------------------------------------------------------------------------
# SUPPORT: install
# ---------------------------------------------------------------------------
# cmake .. -DCMAKE_INSTALL_PREFIX=../_install
# make install
install(TARGETS hello_app DESTINATION bin)
# ALREADY: install(TARGETS hello1_lib DESTINATION lib)
# install(FILES test.h DESTINATION include)

# ---------------------------------------------------------------------------
# SUPPORT: cpack
# ---------------------------------------------------------------------------
include(CPack)
