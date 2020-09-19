# ===========================================================================
# CMAKE: Build one static library
# ===========================================================================

cmake_minimum_required(VERSION 3.12)
list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_SOURCE_DIR}/../cmake")
include("ccache")

set(MASTER_PROJECT OFF)
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    set(MASTER_PROJECT ON)
    project(libhello VERSION 0.2.1 LANGUAGES CXX)
    message(STATUS "USING: CMAKE_VERSION=${CMAKE_VERSION} (MASTER_PROJECT=${PROJECT_NAME})")
    include("cxx.setup_cxx_standard")
    include("cxx.setup_project")
endif()

option(LIBHELLO_BUILD_TESTS "Enable/disable tests for libhello" ${MASTER_PROJECT})
option(LIBHELLO_AUTO_RUN_TESTS "Automatically run tests after build for libhello" OFF)


# ---------------------------------------------------------------------------
# SECTION: Targets -- One Static Library
# ---------------------------------------------------------------------------
# -- HEADER-ONLY LIBRARY: util
add_library(util INTERFACE)
add_library(HELLO::util ALIAS util)
target_include_directories(util
    INTERFACE
        $<INSTALL_INTERFACE:include>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
)

# -- LIBRARY: hello
add_library(hello STATIC)
add_library(HELLO::hello ALIAS hello)
target_sources(hello
    PRIVATE
        src/hello/Responder.cpp
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/src/hello/Responder.hpp
)
target_link_libraries(hello INTERFACE HELLO::util)
target_include_directories(hello
    PUBLIC
        $<INSTALL_INTERFACE:include>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)


# ---------------------------------------------------------------------------
# SECTION: Unittests
# ---------------------------------------------------------------------------
if(LIBHELLO_BUILD_TESTS)
    enable_testing()

    set(TEST_PROGRAMS test_hello_Responder)

    # -- SOLUTION 1: Builds other programs, libs first. Then auto-runs tests.
    if(LIBHELLO_AUTO_RUN_TESTS)
        add_custom_target(tests ALL
            COMMAND ctest
            DEPENDS ${TEST_PROGRAMS}
            COMMENT "AUTO-RUN TESTS with: all")
    endif()

    # -- TEST PROGRAM: test_hello_Responder
    add_executable(test_hello_Responder)
    target_sources(test_hello_Responder PRIVATE
        tests/hello/test_Responder.cpp
    )
    target_link_libraries(test_hello_Responder PRIVATE HELLO::hello)

    # -- TESTS:
    add_test(NAME test_hello_Responder_without_args   COMMAND test_hello_Responder)
    set_tests_properties(test_hello_Responder_without_args PROPERTIES
        PASS_REGULAR_EXPRESSION "RESPONDER: Hello Alice")

    add_test(NAME test_hello_Responder_with_one_arg   COMMAND test_hello_Responder Bob)
    set_tests_properties(test_hello_Responder_with_one_arg PROPERTIES
        PASS_REGULAR_EXPRESSION "RESPONDER: Hello Bob")

    add_test(NAME test_hello_Responder_with_many_args COMMAND test_hello_Responder Alice and Bob)
    set_tests_properties(test_hello_Responder_with_many_args PROPERTIES
        PASS_REGULAR_EXPRESSION "RESPONDER: Hello Alice and Bob")

endif()
# ---------------------------------------------------------------------------
# SUPPORT: install
# ---------------------------------------------------------------------------
# cmake .. -DCMAKE_INSTALL_PREFIX=../_install
# make install
install(TARGETS hello DESTINATION lib)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/src/hello
        DESTINATION include
        FILES_MATCHING PATTERN "*.hpp")
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/src/util
    DESTINATION include
    FILES_MATCHING PATTERN "*.hpp")
# install(FILES src/test.h DESTINATION include)

# ---------------------------------------------------------------------------
# SUPPORT: cpack
# ---------------------------------------------------------------------------
# -- HINT: Simplify testing (avoid: ${CMAKE_SYSTEM_NAME} in package name)
set(CPACK_PACKAGE_NAME "${PROJECT_NAME}")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}_binary")
set(CPACK_SOURCE_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}_source")
include(CPack)
