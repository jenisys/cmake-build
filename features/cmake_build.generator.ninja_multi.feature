Feature: Use cmake_generator "Ninja Multi-Config"

  Background: Setup CMake Workspace
    Given I set the environment variable "CMAKE_BUILD_CONFIG" to "multi_config"
    # Given I set the environment variable "CMAKE_GENERATOR" to "ninja.multi"

  Scenario: Init new-born CMake Project with cmake.generator=ninja.multi
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    And the directory "build.multi_config" does not exist
    When I run "cmake-build init -g ninja.multi"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.multi_config (using cmake.generator=ninja.multi)
      """
    And the command output should contain:
      """
      cmake -G "Ninja Multi-Config" ..
      """
    And the command output should contain:
      """
      Build files have been written to: {__WORKDIR__}/build.multi_config
      """
    And the directory "build.multi_config" should exist
    And the CMake project is initialized for build_config="multi_config"

    # Given I ensure that the CMake project "." is initialized

  Scenario Outline: Build CMake Project with cmake.generator=ninja.multi and config=<cmake_config>
    # Given I use the directory "library_hello" as working directory
    # And I use the CMake project "."
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    When I run "cmake-build init -g ninja.multi"
    When I run "cmake-build build --config=<cmake_config>"
    Then it should pass with:
      """
      cmake --build . --config <cmake_config>
      """
    And the command output should contain:
      """
      Linking CXX static library lib/<cmake_config>/libhello.a
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.multi_config (SKIPPED: Initialized with cmake.generator=ninja.multi)
      """

    Examples:
        | cmake_config |
        | Debug   |
        | Release |
