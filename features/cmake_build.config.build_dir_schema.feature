@fixture.cmake_build.ensure_clean_environment
Feature: config-parameter build_dir_schema

  As a cmake-build user
  I want to specify the cmake.project build_dir name in a flexible way
  So that I can provide multiple build_dir naming variants (and be more flexible).

  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the directory "library_hello/" as working directory
    And I use the CMake project "."


  Scenario: Use default build_dir_schema="build.{BUILD_CONFIG}" if not specified
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    But note that "the default build_dir_schema was used"


  Scenario: Specify build_dir_schema via configfile
    Given a file named "cmake_build.yaml" with:
        """
        build_dir_schema: "build/{BUILD_CONFIG}"
        """
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build/debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ../..
      """
    When I run "cmake-build build"
    Then it should pass with:
      """
      CMAKE-INIT:  build/debug (SKIPPED: Initialized with cmake.generator=ninja).
      CMAKE-BUILD: build/debug
      """
    And the command output should contain:
      """
      cmake --build .
      """

  @fixture.cmake_build.cleanup_environment
  Scenario: Specify build_dir_schema via environment variable
    Given I set the environment variable "CMAKE_BUILD_BUILD_DIR_SCHEMA" to "build_{BUILD_CONFIG}"
    When I run "cmake-build init --build-config=release"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build_release (using cmake.generator=ninja)
      """
    But note that "build_dir_schema from environment variable was used"
