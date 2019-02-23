@fixture.cmake_build.ensure_clean_environment
Feature: config-parameter cmake.generator

  As a cmake-build user
  I want sometimes to specify the cmake.generator that should be used
  So that I build cmake.projects efficiently in my working environment.

  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the directory "library_hello/" as working directory
    And I use the CMake project "."

  Scenario: Use default cmake.generator=ninja if none is specified
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """


  Scenario: Specify cmake.generator via configfile
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: make
        """
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=make)
      """
    But note that "configfile specific cmake.generator=make was used"


  Scenario: Specify cmake.generator via cmdline
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: make
        """
    When I run "cmake-build init --generator=ninja"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    But note that "cmdline overrides configfile"


  @fixture.cmake_build.cleanup_environment
  Scenario: Specify cmake.generator via environment variable
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        """
    Given I set the environment variable "CMAKE_BUILD_CMAKE_GENERATOR" to "make"
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=make)
      """
    But note that "environment specific cmake.generator=make was used"


  Scenario: Use cmake.generator=OTHER on cmdline for initialited cmake.project (Perform: reinit)
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: make
        """
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=make)
      """
    When I run "cmake-build init --generator=ninja"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (NEEDS-REINIT)
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    But note that "cmake.generator=other on cmdline emits NEEDS-REINIT"
