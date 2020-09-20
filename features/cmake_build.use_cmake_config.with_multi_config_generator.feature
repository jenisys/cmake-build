Feature: Use cmake --config option with multi-configuration cmake.generator(s)

  As a CMake build system user
  I want to setup the CMake build project once and then switch between the build configuration
  So that I can easily build Debug/Release/... build configurations.

  . With a multi-configuration cmake.generator you setup the CMake build directory once.
  . The default config is defined by CMAKE_DEFAULT_BUILD_TYPE or CMAKE_CONFIGURATIONS[0].
  . Otherwise, you can explicitly specify which (build) config(uration) should be used,
  . by using:
  .
  .     cmake --config=Debug   ...    # CMake build with config=Debug
  .     cmake --config=Release ...    # CMake build with config=Release
  .
  . USING: cmake.generator="ninja.multi" ("Ninja Multi-Config")
  . CMAKE_GENERATOR="Ninja Multi-Config" is used here as multi-configuration generator.
  .

  Background: Setup CMake Workspace
    Given I set the environment variable "CMAKE_BUILD_CONFIG" to "multi_config"
    # Given I set the environment variable "CMAKE_GENERATOR" to "ninja.multi"

  Scenario: Init new-born CMake Project with cmake.generator=ninja.multi
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    And the directory "build.multi_config" does not exist
    When I run "cmake-build init -g ninja.multi --config=Release"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.multi_config (using cmake.generator=ninja.multi)
      """
    And the command output should contain:
      """
      cmake -G "Ninja Multi-Config" --config Release -DCMAKE_BUILD_TYPE=Release ..
      """
    And the command output should contain:
      """
      Build files have been written to: {__WORKDIR__}/build.multi_config
      """
    And the directory "build.multi_config" should exist
    And the CMake project is initialized for build_config="multi_config"


  Scenario Outline: Build CMake Project with config=<config>
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    When I run "cmake-build init -g ninja.multi"
    When I run "cmake-build build --config=<config>"
    Then it should pass with:
      """
      cmake --build . --config <config>
      """
    And the command output should contain:
      """
      Linking CXX static library lib/<config>/libhello.a
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.multi_config (SKIPPED: Initialized with cmake.generator=ninja.multi)
      """

    Examples:
        | config |
        | Debug   |
        | Release |


  Scenario Outline: Run Tests with config=<config>
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    When I run "cmake-build build -g ninja.multi --config=<config>"
    When I run "cmake-build test --config=<config>"
    Then it should pass with:
      """
      ctest -C <config>
      """
    And the command output should contain "100% tests passed"
    And the command output should contain:
      """
      CMAKE-INIT:  build.multi_config (SKIPPED: Initialized with cmake.generator=ninja.multi).
      CMAKE-TEST:  build.multi_config
      """

    Examples:
        | config |
        | Debug   |
        | Release |


  Scenario Outline: Install build artifacts (variant: config=<config>)
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    When I run "cmake-build build -g ninja.multi --config=<config>"
    When I run "cmake-build install --config=<config> --prefix={CWD}/.installed.<config>"
    Then it should pass with:
      """
      cmake --build . --config <config> --target install
      """
    And the command output should contain:
      """
      cmake -DCMAKE_INSTALL_PREFIX={__WORKDIR__}/.installed.<config> ..
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.multi_config (SKIPPED: Initialized with cmake.generator=ninja.multi).
      CMAKE-INSTALL: build.multi_config
      CMAKE-INSTALL: Use CMAKE_INSTALL_PREFIX={__WORKDIR__}/.installed.<config>
      """

    Examples:
        | config |
        | Debug   |
        | Release |
