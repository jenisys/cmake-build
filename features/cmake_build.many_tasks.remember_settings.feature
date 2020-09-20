Feature: Remember Settings if multiple tasks are used

  As a cmake-build user
  I want to specify configuration only once and
    other tasks on the command-line should inherit it
  So that I need to type less of essential information

  . SPECIFICATION: Remember Settings between multiple tasks
  . CONSTRAINTS:
  .   * Only applies if multiple tasks are used in one cmake-build command
  .   * REMEMBERED: config, build_config
  .   * REMEMBERED settings are only used if the following tasks
  .     does not specify/override this information.

  Background: Setup CMake Workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    # Given I successfully run "cmake-build init -g ninja.multi"

  Scenario: Remember --build-config/-b (CMAKE_BUILD_CONFIG)

    . HINTS:
    .   First  task provides build_config="release" that is remembered.
    .   Second task remembers build_config="release" (from first task).

    When I run "cmake-build init -b release build"
    Then it should pass with
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-BUILD: build.release
      """
    And the command output should contain:
      """
      Linking CXX static library lib/libhello.a
      """

  Scenario: Override remembered --build-config (CMAKE_BUILD_CONFIG)

    . HINTS:
    .   First  task provides build_config="release" that is remembered.
    .   Second task overrides the remembered build_config with "debug".
    .   Third  task remembers build_config="debug" (from second task).

    When I run "cmake-build init -b release build -b debug test"
    Then it should pass with
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-BUILD: build.debug
      """
    And the command output should contain:
      """
      CMAKE-TEST:  build.debug
      """

  Scenario: Remember --config (CMAKE_CONFIG)

    . HINTS:
    .   First  task provides build_config="release" that is remembered.
    .   Second task remembers build_config="release" (from first task).

    Given I set the environment variable "CMAKE_BUILD_CONFIG" to "multi"
    When I run "cmake-build init -g ninja.multi --config=Release build"
    Then it should pass with
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.multi (using cmake.generator=ninja.multi)
      """
    And the command output should contain:
      """
      cmake -G "Ninja Multi-Config" --config Release -DCMAKE_BUILD_TYPE=Release ..
      """
    And the command output should contain:
      """
      cmake --build . --config Release
      """
    And the command output should contain:
      """
      Linking CXX static library lib/Release/libhello.a
      """

  Scenario: Override remembered --config (CMAKE_CONFIG)

    . HINTS:
    .   build: First  task provides config="Release" that is remembered.
    .   clean: Second task remembers config="Release" (and removes Release artifacts).
    .   build: Third task overrides the remembered config with "Debug".
    .   test:  Fourth task remembers config="Debug" (from second task).

    Given I set the environment variable "CMAKE_BUILD_CONFIG" to "multi"
    When I run "cmake-build init -g ninja.multi"
    Then it should pass with
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.multi (using cmake.generator=ninja.multi)
      """
    When I run "cmake-build build --config=Release clean build --config=Debug test"
    Then it should pass with
      """
      cmake --build . --config Release
      """
    And the command output should contain:
      """
      Linking CXX executable bin/Release/test_hello_Responder
      """
    And the command output should contain:
      """
      cmake --build . --config Release -- clean
      """
    And the command output should contain:
      """
      cmake --build . --config Debug
      """
    And the command output should contain:
      """
      Linking CXX executable bin/Debug/test_hello_Responder
      """
    And the command output should contain "ctest -C Debug"
    And the command output should contain "100% tests passed"
