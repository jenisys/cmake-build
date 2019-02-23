@fixture.cmake_build.ensure_clean_environment
Feature: Specify the default build_config (name)

  As a cmake-build user
  I want to specify the name of my default build-config
  So that the cmake-build command-line is simpler/shorter in most cases.

  NOTE: The default build_config is "debug" even if configfile is missing.


  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the CMake project "library_hello"
    And I use the directory "library_hello/" as working directory
    And a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        build_configs:
          - debug
          - release:
              cmake_build_type: MinSizeRel
              cmake_defines:
                - FOO: foo
          - release2
          - release3
        """


  Scenario: Use default build_config=debug
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """

  Scenario: Use configfile to specify default build_config
    Given a file named "cmake_build.yaml" with:
        """
        build_config:  release2
        build_configs:
          - debug
          - release2
        """
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release2 (using cmake.generator=ninja)
      """

  @fixture.cmake_build.cleanup_environment
  Scenario: Use environment variable to specify default build_config
    Given I set the environment variable "CMAKE_BUILD_CONFIG" to "release"
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release (using cmake.generator=ninja)
      """
