Feature: cmake-build without Config-File inherits Config-File

  As a cmake build user
  I want to inherit a "cmake-build config-file" from a parent directory
  So that
  ... I can use a parent config-file in all sub-projects.
  ... I can easily work in a sub-ordinate directory and use it (build-configs, toolchains, ...).

  . SPECIFICATION: Config-File Inheritance Mechanism
  . If the current directory does not contain a config-file ("cmake_build.yaml"):
  .   * a config-file from a parent directory is inherited (if one exists)
  .   * All parent directories up to the root-directory are searched
  .   * Uses environment-variable CMAKE_BUILD_INHERIT_CONFIG_FILE : bool.as_string = "yes"
  .   * If the environment-variable is not defined, its value is true ("yes").
  .   * Use CMAKE_BUILD_INHERIT_CONFIG_FILE="no" to disable the inheritance mechanism.

  Background: Setup CMake Workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory


  @fixture.cmake_build.ensure_clean_environment
  Scenario: cmake-build inherits config-file from parent-directory
    Given the environment variable "CMAKE_BUILD_INHERIT_CONFIG_FILE" does not exist
    And   a file named "CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    And   a file named "../cmake_build.yaml" with:
      """
      build_configs:
        - inherited.one:
            cmake_generator: ninja.multi
      """
    When I run "cmake-build init --build-config=inherited.one"
    Then it should pass with:
      """
      CMAKE-BUILD: Using ../cmake_build.yaml (for DEFAULTS)
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.inherited.one (using cmake.generator=ninja.multi)
      """
    And the CMake project is initialized for build_config="inherited.one"
    But note that "it inherited the build-config settings from the config-file in the parent directory"
    And note that "it inherited the cmake.generator=ninja.multi from the config-file in the parent directory"

  @fixture.cmake_build.ensure_clean_environment
  Scenario: cmake-build with CMAKE_BUILD_INHERIT_CONFIG_FILE=yes
    Given I set the environment variable "CMAKE_BUILD_INHERIT_CONFIG_FILE" to "yes"
    and   a file named "CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    And   a file named "../cmake_build.yaml" with:
      """
      build_configs:
        - inherited.one:
            cmake_generator: ninja.multi
      """
    When I run "cmake-build init --build-config=inherited.one"
    Then it should pass with:
      """
      CMAKE-BUILD: Using ../cmake_build.yaml (for DEFAULTS)
      """
    And the command output should contain:
      """
      CMAKE-INIT:  build.inherited.one (using cmake.generator=ninja.multi)
      """
    And the CMake project is initialized for build_config="inherited.one"
    But note that "it inherited the build-config settings from the config-file in the parent directory"
    And note that "it inherited the cmake.generator=ninja.multi from the config-file in the parent directory"

  @fixture.cmake_build.ensure_clean_environment
  Scenario: cmake-build with CMAKE_BUILD_INHERIT_CONFIG_FILE=no
    Given I set the environment variable "CMAKE_BUILD_INHERIT_CONFIG_FILE" to "no"
    and   a file named "CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    And   a file named "../cmake_build.yaml" with:
      """
      build_configs:
        - inherited.one:
            cmake_generator: ninja.multi
      """
    When I run "cmake-build init --build-config=inherited.one"
    Then it should fail with:
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      UNKNOWN BUILD-CONFIG: inherited.one (expected: debug, release)
      """
    And the command output should not contain:
      """
      CMAKE-BUILD: Using ../cmake_build.yaml (for DEFAULTS)
      """
    But note that "it inherited the build-config settings from the config-file in the parent directory"
    And note that "it inherited the cmake.generator=ninja.multi from the config-file in the parent directory"


  @fixture.cmake_build.ensure_clean_environment
  Scenario: cmake-build using cmake_toolchain from inherited config-file

    ENSURE: cmake_toolchain value (as path) is evaluated relative to the config-file directory.

    Given a file named "CMakeLists.txt" exists
    And   a file named "cmake_build.yaml" does not exist
    And   a file named "../cmake_build.yaml" with:
      """
      build_configs:
        - inherited.debug:
            cmake_toolchain: cmake/fake_toolchain.cmake
      """
    And   a file named "../cmake/fake_toolchain.cmake" with:
      """
      include_guard(DIRECTORY)
      message(STATUS "USING: FAKE-TOOLCHAIN")
      """
    When I run "cmake-build init --build-config=inherited.debug"
    Then it should pass with:
      """
      CMAKE-BUILD: Using ../cmake_build.yaml (for DEFAULTS)
      """
    And the command output should contain "USING: FAKE-TOOLCHAIN"
    And the command output should contain:
      """
      CMAKE-INIT:  build.inherited.debug (using cmake.generator=ninja)
      """
    And the CMake project is initialized for build_config="inherited.debug"
    But note that "it inherited the build-config settings from the config-file in the parent directory"
    And note that "it inherited the cmake.generator=ninja.multi from the config-file in the parent directory"


  @fixture.cmake_build.ensure_clean_environment
  Scenario: cmake-build using --project option (next to cmake-project-dir)
    Given I ensure that the directory "../other" exists
    Given I use the directory "../other" as working directory
    And   a file named "../library_hello/CMakeLists.txt" exists
    And   a file named "../library_hello/cmake_build.yaml" does not exist
    And   a file named "../cmake_build.yaml" with:
      """
      build_configs:
        - inherited.one:
            cmake_generator: ninja.multi
      """
    When I run "cmake-build init --project=../library_hello --build-config=inherited.one"
    Then it should pass with:
      """
      CMAKE-BUILD: Using ../cmake_build.yaml (for DEFAULTS)
      """
    But note that "it discoverd the config-file in the current-directory: (as CONFIG)"
    And the command output should contain:
      """
      CMAKE-INIT:  ../library_hello/build.inherited.one (using cmake.generator=ninja.multi)
      """
    But note that "it used the config-file in the parent-directory for another cmake-project"
    And note that "it used the cmake.generator=ninja.multi from the config-file"

  @fixture.cmake_build.ensure_clean_environment
  Scenario: cmake-build using --project option (from parent-dir)
    Given I use the directory ".." as working directory
    And   a file named "library_hello/CMakeLists.txt" exists
    And   a file named "library_hello/cmake_build.yaml" does not exist
    And   a file named "cmake_build.yaml" with:
      """
      build_configs:
        - inherited.one:
            cmake_generator: ninja.multi
      """
    When I run "cmake-build init --project=library_hello --build-config=inherited.one"
    Then it should pass with:
      """
      CMAKE-BUILD: Using cmake_build.yaml (as CONFIG)
      """
    But note that "it discoverd the config-file in the current-directory: (as CONFIG)"
    And the command output should contain:
      """
      CMAKE-INIT:  library_hello/build.inherited.one (using cmake.generator=ninja.multi)
      """
    And the command output should contain:
      """
      Build files have been written to: {__WORKDIR__}/library_hello/build.inherited.one
      """
    And the CMake project is initialized for build_config="inherited.one"
    But note that "it used the config-file in the current-directory for a sub-ordinate project"
    And note that "it used the cmake.generator=ninja.multi from the config-file"
