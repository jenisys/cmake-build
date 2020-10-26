Feature: cmake-build reinit Command (without cmake-build config-file)

  As a cmake build user
  I want to re-initialize a CMake project to recreate its build directory
  So that I have a clean initial state (maybe: with another cmake.generator).

  . RELATED: features/cmake_build.init.feature
  .
  . SPECIFICATION: Reinit
  .   * Recreates the CMake project build directory (CMAKE_BINARY_DIR).
  .   * Inherits the cmake.generator that was used before (if none is specified).
  .     REASON: Preserve user setup of the CMake project.
  .   * Can override the cmake.generator to use another one.
  .
  . DIRECTORY STRUCTURE:
  .   WORKDIR/
  .       +-- CMAKE_PROJECT_1/                CMake project directory for "CMAKE_PROJECT_1".
  .       |     +-- build.debug/              CMake project build_dir for build_config=debug
  .       |     +-- build.release/            CMake project build_dir for build_config=release
  .       |     +-- CMakeLists.txt            CMake description for "CMAKE_PROJECT_1".

  Background: Setup CMake Workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory


  @fixture.cmake_build.inherit_config_file.disabled
  Scenario: CMake Project (build dir) does not exist (new-born)
    Given the directory "build.debug" does not exist
    When I run "cmake-build reinit"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the command output should contain:
      """
      uild files have been written to: {__WORKDIR__}/build.debug
      """
    And the CMake project is initialized with build_config="debug"
    And the directory "build.debug" should exist
    But note that "build_config=debug is used per default (CMAKE_BUILD_CONFIG)"
    And note that "cmake.generator=ninja is used per default"


  @fixture.cmake_build.inherit_config_file.disabled
  Scenario: CMake Project build_dir exists and is initialized (recreate it)
    Given I set the environment variable "CMAKE_BUILD_CONFIG" to "release"
    When I run "cmake-build init --generator=make"
    Then the CMake project is initialized with build_config="release"
    But note that "INTERESTING PART: Starts now"
    When I run "cmake-build reinit"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release (using cmake.generator=make)
      """
    And the command output should contain:
      """
      cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release ..
      """
    And the CMake project is initialized with build_config="release"
    But note that "reinit inherits the cmake.generator (that was used before)"


  @fixture.cmake_build.inherit_config_file.disabled
  Scenario: Existing CMake Project is re-initialized with another cmake.generator
    Given I set the environment variable "CMAKE_BUILD_CONFIG" to "release"
    When I run "cmake-build init --generator=make"
    Then the CMake project is initialized with build_config="release"
    But note that "INTERESTING PART: Starts now"
    When I run "cmake-build reinit --generator=ninja"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Release ..
      """
    And the CMake project is initialized with build_config="release"
    But note that "reinit overrides the cmake.generator (that was used before)"


  Scenario: CMake Project directory does not exist (skip-and-fail)
    Given I use the directory ".." as working directory
    And  I remove the directory "library_hello/"
    When I run "cmake-build reinit"
    Then it should fail with:
      """
      CMAKE-BUILD: Ignore . (not a cmake.project; cwd={__WORKDIR__})
      CMAKE-BUILD: OOPS, no projects are specified (STOP HERE).
      """
