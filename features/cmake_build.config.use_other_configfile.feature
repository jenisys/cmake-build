@fixture.cmake_build.ensure_clean_environment
Feature: Use another configfile name

  As a cmake-build user
  I want sometimes to use another configfile name
  So that I can provide multiple config variants and be more flexible.

  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the directory "library_hello/" as working directory
    And I use the CMake project "."
    And a file named "other.yaml" with:
        """
        cmake_generator: make
        build_configs:
          - debug
          - release
        """

  Scenario: Specify other configfile on cmdline
    When I run "cmake-build -f other.yaml init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=make)
      """
    But note that "configfile specific cmake.generator=make was used"


  @fixture.cmake_build.cleanup_environment
  Scenario: Specify other configfile via environment variable
    Given I set the environment variable "INVOKE_RUNTIME_CONFIG" to "other.yaml"
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=make)
      """
    But note that "configfile specific cmake.generator=make was used"
