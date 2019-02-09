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
      CMake Error: The source directory "/Users/jens/se/cmake-build/__WORKDIR__/library_hello" does not appear to contain CMakeLists.txt.
      """

  Scenario: cmake-build works without configfile and build-config=debug

    INTENTION: Support build-config=debug even when no configfile exists.

    Given a file named "library_hello/CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build init --project=library_hello --build-config=debug"
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


  Scenario: cmake-build works without configfile and build-config=release

    INTENTION: Support build-config=release even when no configfile exists.

    Given a file named "library_hello/CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    When I run "cmake-build init --project=library_hello --build-config=release"
    Then it should pass with:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.release
      """
    And the command output should contain:
      """
      CMAKE-INIT:  library_hello/build.release (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Release ..
      """
    And I use the CMake project "library_hello" with build_config="release"
    And the CMake project is initialized


  Scenario: cmake-build fails without configfile if other build-config is used

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
