# ===========================================================================
# CMAKE: Build one program
# ===========================================================================

cmake_minimum_required(VERSION 3.12)
list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_SOURCE_DIR}/../cmake")
include("ccache")

set(MASTER_PROJECT OFF)
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    project(hello VERSION 0.2.0 LANGUAGES CXX)
    message(STATUS "USING: CMAKE_VERSION=${CMAKE_VERSION} (MASTER_PROJECT=${PROJECT_NAME})")
    set(MASTER_PROJECT ON)
    include("cxx.setup_cxx_standard")
    include("cxx.setup_project")
endif()


option(BUILD_TESTING "Enable/disable tests for hello" ${MASTER_PROJECT})
# DISABLED: option(LIBHELLO_BUILD_TESTS "Enable/disable tests for libhello" OFF)



# ---------------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------------
if(NOT TARGET HELLO::hello)
    add_subdirectory("../library_hello" "library_hello")
endif()


# ---------------------------------------------------------------------------
# SECTION: Targets -- One Executable/Programm
# ---------------------------------------------------------------------------
add_executable(hello_app
    hello_main.cpp
)
target_link_libraries(hello_app HELLO::hello)
set_property(TARGET hello_app PROPERTY EchoString "CXX-BUILD: hello_app ...")


# ---------------------------------------------------------------------------
# SECTION: TESTS
# ---------------------------------------------------------------------------
if(BUILD_TESTING)
    enable_testing()

    # -- TESTS:
    add_test(NAME test_hello.without_args   COMMAND hello_app)
    set_tests_properties(test_hello.without_args PROPERTIES
        PASS_REGULAR_EXPRESSION "RESPONDER: Hello Alice")

    add_test(NAME test_hello.Alice   COMMAND hello_app Alice)
    set_tests_properties(test_hello.Alice PROPERTIES
        PASS_REGULAR_EXPRESSION "RESPONDER: Hello Alice")

    add_test(NAME test_hello.Alice_and_Bob  COMMAND hello_app Alice and Bob)
    set_tests_properties(test_hello.Alice_and_Bob PROPERTIES
        PASS_REGULAR_EXPRESSION "RESPONDER: Hello Alice and Bob")
endif()

# -- AUTO-RUN TARGET:
# add_custom_target(run-hello ALL
#     COMMAND hello_app ${HELLO_ARGS}
#     DEPENDS hello_app
#     COMMENT "AUTO-RUN: hello_app (EXPECTED-OUTPUT: ${HELLO_EXPECTED_OUTPUT})")

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
