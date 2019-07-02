@fixture.cmake_build.ensure_clean_environment
Feature: Use build_config name to select build-config dataset

  As a cmake-build user
  I want to use a simple build-config name to select a canned recipe dataset
  So that the setup/init of the cmake.project build_dir is simplified

  . SPECIFICATION:
  .  DEFAULT BUILD_CONFIG: "debug"
  .  BUILD_CONFIGS:
  .     Predefined:   "debug", "release"
  .     Host aliases: "host_debug", "host_release"
  .
  .  NOTES:
  .   * cmake_build_type (CMAKE_BUILD_TYPE) is auto-discovered from name
  .     if none is specified for a build_config (for: "...debug...", "...release...").
  .     Discovery is case-insensitive.
  .
  . RELATED:
  .  * cmake_build.build_config.specify_default.feature
  .  * cmake_build.build_config.discover4host_platform.*.feature


  Background: Setup CMake Workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    # -- SAME-AS:
    #  Given a new working directory
    #  And I copy the directory "examples/cmake/" to the working directory
    #  And I copy the CMake project "examples/library_hello/" to the working directory
    #  And I use the CMake project "library_hello"
    #  And I use the directory "library_hello/" as working directory
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
        """


  Scenario: Use default build_config=debug
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """

  Scenario: Use cmdline to specify build_config
    When I run "cmake-build init --build-config=release2"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release2 (using cmake.generator=ninja)
      """

  Scenario: build_config dataset is used during init
    When I run "cmake-build init --build-config=release"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.release (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=MinSizeRel -DFOO=foo ..
      """

  Scenario: Unknown build_config should cause failure
    When I run "cmake-build init --build-config=UNKNOWN"
    Then it should fail with:
      """
      UNKNOWN BUILD-CONFIG: UNKNOWN (expected: debug, release, release2)
      """
