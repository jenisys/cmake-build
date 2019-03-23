@fixture.cmake_build.ensure_clean_environment
Feature: Use build_config=all as alias for all build_configs

  As a cmake-build user
  I want to build all build_configs
  So that certain use cases are extremely simple

  . SPECIFICATION:
  .  With configfile: Configured build_configs are used.
  .
  .     build_configs = configfile.build_configs   # HINT: Names.
  .
  .  Without configfile:
  .
  .     build_configs = ["debug", "release"]
  .
  .   If CMAKE_BUILD_CONFIG environment variable is defined and starts with "host_":
  .
  .     build_configs = ["host_debug", "host_release"]

  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the CMake project "library_hello"
    And I use the directory "library_hello/" as working directory


  Scenario: Use build_config=all on command-line with configfile
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        build_configs:
          - debug
          - release
          - release2:
              cmake_build_type: MinSizeRel
        """
    When I run "cmake-build init --build-config=all"
    Then it should pass with:
      """
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.release (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.release2 (using cmake.generator=ninja)
      """

  Scenario: Use build_config=all on command-line without configfile
    When I run "cmake-build init --build-config=all"
    Then it should pass with:
      """
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.release (using cmake.generator=ninja)
      """
