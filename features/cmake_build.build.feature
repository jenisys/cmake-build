@fixture.cmake_build.inherit_config_file.disabled
Feature: cmake-build build Command

  As a cmake build user
  I want to use CMake as (macro) build system without need
  to manually initialize the build system (by generating it with CMake)
  So that I directly build independent of the CMake project's initialized state.
  (and I do need to remember the parameters or do the manual steps).

  Background: Setup CMake Workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory

  # -- SAME AS:
  #  Given a new working directory
  #  And I copy the directory "examples/cmake/" to the working directory
  #  And I copy the CMake project "examples/library_hello/" to the working directory
  #  And I use the directory "library_hello/" as working directory
  #  And I use the CMake project "."


  Scenario: CMake Project (build dir) does not exist (perform: init before build)
    Given the directory "build.debug" does not exist
    When I run "cmake-build build"
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
      CMAKE-BUILD: build.debug
      """
    And the directory "build.debug" should exist
    And the CMake project is initialized for build_config="debug"


  @fixture.cmake_build.inherit_config_file.disabled
  Scenario: CMake Project (build dir) exists but is not initialized (perform: init before build)
    Given I ensure that the directory "build.debug" exists
    And the CMake project is not initialized
    When I run "cmake-build build"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (NEEDS-REINIT)
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the command output should contain:
      """
      CMAKE-BUILD: build.debug
      """
    And the directory "build.debug" should exist
    And the CMake project is initialized for build_config="debug"

  Scenario: CMake Project (build dir) exists and is initialized (skip: init before build)
    When I successfully run "cmake-build init"
    Then the CMake project is initialized
    When I run "cmake-build build"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (SKIPPED: Initialized with cmake.generator=ninja).
      """
    And the command output should not contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the command output should contain:
      """
      CMAKE-BUILD: build.debug
      """

  @fixture.cmake_build.inherit_config_file.disabled
  Scenario: CMake Project (build dir) is initialized and should use another cmake.generator (perform: init before build)
    When I successfully run "cmake-build init"
    Then the CMake project is initialized
    When I run "cmake-build build --generator=make"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (NEEDS-REINIT)
      CMAKE-INIT:  build.debug (using cmake.generator=make)
      """
    And the command output should contain:
      """
      cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the command output should contain:
      """
      CMAKE-BUILD: build.debug
      """
    Then the CMake project is initialized

  Scenario: CMake Project (directory) has no "CMakeLists.txt" file (fail: not a cmake_project)
    When I remove the file "CMakeLists.txt"
    When I run "cmake-build build"
    Then it should fail with:
      """
      CMAKE-BUILD: Ignore . (not a cmake.project; cwd={__WORKDIR__})
      CMAKE-BUILD: OOPS, no projects are specified (STOP HERE).
      """
    Then the CMake project is not initialized

  Scenario: CMake Project (directory) does not exist (fail: not a cmake_project)
    When I run "cmake-build build --project=UNKNOWN_DIR"
    Then it should fail with:
      """
      CMAKE-BUILD: UNKNOWN_DIR (SKIPPED: cmake.project directory does not exist)
      """
