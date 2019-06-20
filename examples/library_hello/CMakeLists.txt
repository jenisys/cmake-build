# ===========================================================================
# CMAKE: Build one static library
# ===========================================================================

cmake_minimum_required(VERSION 3.12)
include("${CMAKE_CURRENT_SOURCE_DIR}/../cmake/toolchain.optional/ccache.cmake")
project(libhello VERSION 0.1.0 LANGUAGES CXX)

set(_TOPDIR "${PROJECT_SOURCE_DIR}/..")
include(${_TOPDIR}/cmake/project.setup_cxx.cmake)

# ---------------------------------------------------------------------------
# SECTION: Targets -- One Static Library
# ---------------------------------------------------------------------------
# -- LIBRARY: hello
add_library(hello STATIC
    src/hello/Responder.cpp
)
add_library(HELLO::hello ALIAS hello)
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
# enable_testing()

set(TEST_PROGRAMS test_hello_Responder)

# -- SOLUTION 1: Builds other programs, libs first. Then auto-runs tests.
set(RUN_AUTO_TESTS ON)
if(RUN_AUTO_TESTS)
    add_custom_target(tests ALL
        COMMAND ctest
        DEPENDS ${TEST_PROGRAMS}
        COMMENT "AUTO-RUN TESTS with: all")
endif()

# -- TEST PROGRAM: test_hello_Responder
add_executable(test_hello_Responder
    test/hello/test_Responder.cpp
)
target_link_libraries(test_hello_Responder HELLO::hello)

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


# ---------------------------------------------------------------------------
# SUPPORT: install
# ---------------------------------------------------------------------------
# cmake .. -DCMAKE_INSTALL_PREFIX=../_install
# make install
install(TARGETS hello DESTINATION lib)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/src/hello
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
