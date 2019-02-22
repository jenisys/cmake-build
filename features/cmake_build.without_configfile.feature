Feature: cmake-build without Configuration File

  As a cmake build user
  I want to use "cmake-build" anywhere where "cmake" can be used
  So that I can perform a cmake host build even when no configuration file exists

  REASON: Simplify use at non-indended places (and behave more like a build tool).
  REQUIRE: "CMakeLists.txt" file in the CMake project directory (only).
  NOTE: Cross-compiling requires configuration data (toolchain, ...).

  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the CMake project "library_hello"


  @simple_use
  Scenario: cmake-build works without cmdline and configfile if CMakeLists.txt file exists
    Given I use the directory "library_hello/" as working directory
    And   a file named "CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build"
    Then it should pass with:
      """
      -- Build files have been written to: {__WORKDIR__}/build.debug
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the CMake project is initialized for build_config="debug"
    But note that "I can use cmake-build for any CMake project (unprepared)"


  Scenario: cmake-build works without configfile if CMakeLists.txt file exists
    Given a file named "library_hello/CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build init -p library_hello"
    Then it should pass with:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.debug
      """
    And the command output should contain:
      """
      CMAKE-INIT:  library_hello/build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the CMake project is initialized
    But note that "I can use cmake-build for any CMake project (unprepared)"

  Scenario: cmake-build fails without configfile and CMakeLists.txt file
    Given I remove the file "library_hello/CMakeLists.txt"
    And   a file named "library_hello/CMakeLists.txt" does not exist
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build init -p library_hello"
    Then it should fail with:
      """
      CMAKE-INIT: library_hello (SKIPPED: not a cmake.project (missing: CMakeLists.txt file))
      """
      # OLD: CMake Error: The source directory "{__WORKDIR__}/library_hello" does not appear to contain CMakeLists.txt.


  @build_config
  @build_config.<BUILD_CONFIG>
  Scenario Outline: cmake-build works without configfile (case: build-config=<BUILD_CONFIG>)

    INTENTION: Support build-config=<BUILD_CONFIG> even when no configfile exists.

    Given a file named "library_hello/CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build init --project=library_hello --build-config=<BUILD_CONFIG>"
    Then it should pass with:
      """
      CMAKE-INIT:  library_hello/build.<BUILD_CONFIG> (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=<EXPECTED_CMAKE_BUILD_TYPE> ..
      """
    And I use the CMake project "library_hello" with build_config="<BUILD_CONFIG>"
    And the CMake project is initialized

    Examples:
      | BUILD_CONFIG | EXPECTED_CMAKE_BUILD_TYPE |
      | debug        | Debug                     |
      | release      | Release                   |


  @build_config.other
  Scenario: cmake-build fails without configfile using other build-config

    ENSURE: Only build-config= debug, release work automatically without configfile.

    Given a file named "library_hello/CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build init --project=library_hello --build-config=OTHER"
    Then it should fail with:
      """
      UNKNOWN BUILD-CONFIG: OTHER (expected: debug, release)
      """
    And I use the CMake project "library_hello" with build_config="OTHER"
    And the CMake project is not initialized


  @build_config
  @build_config.<BUILD_CONFIG>
  Scenario Outline: cmake-build cleanup works without configfile (case: build-config=<BUILD_CONFIG>)

    Given I use the directory "library_hello/" as working directory
    Given a file named "CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build init --build-config=<BUILD_CONFIG>"
    Then it should pass with:
      """
      Build files have been written to: {__WORKDIR__}/build.<BUILD_CONFIG>
      """
    Then the directory "build.<BUILD_CONFIG>" should exist
    And note that "INTERESTING-PART: Starts here"
    When I run "cmake-build cleanup"
    Then it should pass with:
      """
      RMTREE: build.<BUILD_CONFIG>
      """
    And the directory "build.<BUILD_CONFIG>" should not exist

    Examples:
      | BUILD_CONFIG |
      | debug     |
      | release   |
