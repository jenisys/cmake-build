Feature: cmake-build install Command

  As a cmake build user
  I want to install build artifacts to the predefined location
  or a new user-defined location

  . SPECIFICATION:
  .   The CMake variable CMAKE_INSTALL_PREFIX is used to define
  .   the location (base-directory) where the artifacts should be installed.
  .
  .   CONFIGFILE:
  .     cmake_install_prefix: PATH        # OPTION 1: Default for all BUILD_CONFIGs
  .     build_configs:
  .       - debug:
  .           cmake_install_prefix: PATH  # OPTION 2: For a specific BUILD_CONFIG
  .
  .   PLACEHOLDERS in "cmake_install_prefix" parameter:
  .     The following placeholders are supported in "cmake_install_prefix":
  .
  .     - BUILD_CONFIG: Name of the current BUILD_CONFIG value
  .     - CMAKE_BUILD_TYPE: Current value of CMAKE_BUILD_TYPE (Debug, Release, ...)
  .     - HOME: Absolute path to the HOME directory of the current user.
  .
  .   PLACEHOLDER EXAMPLE:
  .     cmake_install_prefix: {HOME}/.local/{BUILD_CONFIG}

  # -- OLD:
  #    Given a new working directory
  #    And I copy the directory "examples/cmake/" to the working directory
  #    And I copy the CMake project "examples/library_hello/" to the working directory
  #    And I use the directory "library_hello/" as working directory
  #    And I use the CMake project "."
  Background: Setup CMake Workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory


  Scenario: Use install if project is not build yet (perform: init, build, install)
    Given the directory "build.debug" does not exist
    When I run "cmake-build install --prefix=LOCAL.{BUILD_CONFIG}"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-INSTALL: build.debug
      CMAKE-INSTALL: Use CMAKE_INSTALL_PREFIX=LOCAL.debug
      """
    And the command output should contain:
      """
      -- Install configuration: "Debug"
      -- Installing: {__WORKDIR__}/build.debug/LOCAL.debug/lib/libhello.a
      -- Installing: {__WORKDIR__}/build.debug/LOCAL.debug/include/hello
      -- Installing: {__WORKDIR__}/build.debug/LOCAL.debug/include/hello/Responder.hpp
      """
    And the directory "build.debug/LOCAL.debug" should exist


  Scenario: Use install if project is already build (perform: install)
    Given the directory "build.debug" does not exist
    When I successfully run "cmake-build build"
    When I run "cmake-build install --prefix=LOCAL.{BUILD_CONFIG}_2"
    Then it should pass with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (SKIPPED: Initialized with cmake.generator=ninja).
      CMAKE-INSTALL: build.debug
      CMAKE-INSTALL: Use CMAKE_INSTALL_PREFIX=LOCAL.debug_2
      """
    And the command output should contain:
      """
      -- Installing: {__WORKDIR__}/build.debug/LOCAL.debug_2/lib/libhello.a
      -- Installing: {__WORKDIR__}/build.debug/LOCAL.debug_2/include/hello
      -- Installing: {__WORKDIR__}/build.debug/LOCAL.debug_2/include/hello/Responder.hpp
      """
    And the directory "build.debug/LOCAL.debug_2" should exist


  Scenario: Use install with cmake_install_prefix in config-file for all build-configs
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        cmake_install_prefix: CONFIGFILE_1.{BUILD_CONFIG}
        """
    When I run "cmake-build build"
    Then it should pass with:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=CONFIGFILE_1.debug ..
      """
    When I run "cmake-build install"
    Then it should pass with:
      """
      CMAKE-INSTALL: build.debug
      """
    And the command output should contain:
      """
      -- Install configuration: "Debug"
      -- Installing: {__WORKDIR__}/build.debug/CONFIGFILE_1.debug/lib/libhello.a
      -- Installing: {__WORKDIR__}/build.debug/CONFIGFILE_1.debug/include/hello
      -- Installing: {__WORKDIR__}/build.debug/CONFIGFILE_1.debug/include/hello/Responder.hpp
      """
    And the directory "build.debug/CONFIGFILE_1.debug" should exist


  Scenario: Use install with cmake_install_prefix in config-file for current build-config
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        cmake_install_prefix: CONFIGFILE_1.{BUILD_CONFIG}
        build_configs:
          - debug:
              cmake_install_prefix: CONFIGFILE_2.{BUILD_CONFIG}
              cmake_defines:
                - BUILD_TESTING: no
        """
    When I successfully run "cmake-build build"
    When I run "cmake-build install"
    Then it should pass with:
      """
      CMAKE-INSTALL: build.debug
      """
    And the command output should contain:
      """
      -- Installing: {__WORKDIR__}/build.debug/CONFIGFILE_2.debug/lib/libhello.a
      -- Installing: {__WORKDIR__}/build.debug/CONFIGFILE_2.debug/include/hello
      -- Installing: {__WORKDIR__}/build.debug/CONFIGFILE_2.debug/include/hello/Responder.hpp
      """
    And the directory "build.debug/CONFIGFILE_2.debug" should exist
    But note that "BUILD_CONFIG specific parameter overrides the generic param"


  Scenario: Use install with command-line prefix option to override current cmake_install_prefix
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        cmake_install_prefix: CONFIGFILE_1.{BUILD_CONFIG}
        build_configs:
          - debug:
              cmake_install_prefix: CONFIGFILE_2.{BUILD_CONFIG}
        """
    When I run "cmake-build build"
    Then it should pass with:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=CONFIGFILE_2.debug ..
      """
    When I run "cmake-build install --prefix=CMDLINE.{BUILD_CONFIG}"
    Then it should pass with:
      """
      CMAKE-INSTALL: build.debug
      """
    And the command output should contain:
      """
      -- Install configuration: "Debug"
      -- Installing: {__WORKDIR__}/build.debug/CMDLINE.debug/lib/libhello.a
      -- Installing: {__WORKDIR__}/build.debug/CMDLINE.debug/include/hello
      -- Installing: {__WORKDIR__}/build.debug/CMDLINE.debug/include/hello/Responder.hpp
      """
    And the directory "build.debug/CMDLINE.debug" should exist
    But note that "command-line parameter overrides the preconfigured configfile params"


  @placeholders
  Scenario Outline: Use install with cmake_install_prefix placeholder=<placeholder>
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        cmake_install_prefix: PLACEHOLDER.<placeholder>
        """
    When I run "cmake-build install --build-config=<BUILD_CONFIG>"
    Then it should pass with:
      """
      CMAKE-INSTALL: build.<BUILD_CONFIG>
      """
    And the command output should contain:
      """
      -- Installing: {__WORKDIR__}/build.<BUILD_CONFIG>/PLACEHOLDER.<value>/lib/libhello.a
      -- Installing: {__WORKDIR__}/build.<BUILD_CONFIG>/PLACEHOLDER.<value>/include/hello
      -- Installing: {__WORKDIR__}/build.<BUILD_CONFIG>/PLACEHOLDER.<value>/include/hello/Responder.hpp
      """
    And the directory "build.<BUILD_CONFIG>/PLACEHOLDER.<value>" should exist

    Examples:
      | placeholder         | value    | BUILD_CONFIG |
      | {BUILD_CONFIG}      | release  | release      |
      | {CMAKE_BUILD_TYPE}_ | Release_ | release      |

