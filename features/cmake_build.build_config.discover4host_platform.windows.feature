@use.with_cmake_system=Windows
@use.with_cmake_cpu=AMD64
Feature: cmake-build auto-discover build_config name on host platform

  As a cmake build user
  I want to auto-discover the build_config name of a host platform (with a schema)
  So that I can distinguish the cmake_project.build_dir on a shared drive
  that is used by several platforms (like: Windows, Linux).

  . SPECIFICATION:
  .   * A host-platform specific build_config name should be automatically discoverable
  .   * The build_configs "host_debug", "host_release" are used as
  .     aliases for the automatically discovered host platform properties
  .   * The host_platform.build_config_schema should support something like:
  .       "{SYSTEM}_{CPU}_{BUILD_TYPE}" or "{SYSTEM}_{PROCESSOR}_{BUILD_TYPE}"
  .
  .       EXAMPLES: On Linux OS with Intel processor (64-bit; CPU=x86_64)
  .         build_config=host_debug:    "Linux_x86_64_debug"
  .         build_config=host_release:  "Linux_x86_64_release"
  .
  .       EXAMPLES: On Linux OS with ARMv8 processor (64-bit), like  ARM Cortex A-53 (CPU=aarch64)
  .         build_config=host_debug:    "Linux_aarch64_debug"
  .         build_config=host_release:  "Linux_aarch64_release"
  .
  .       EXAMPLES: On macOS with Intel processor (64-bit)
  .         build_config=host_debug:    "Darwin_x86_64_debug"
  .         build_config=host_release:  "Darwin_x86_64_release"
  .
  .       EXAMPLES: On Window OS with Intel processor (64-bit)
  .         build_config=host_debug:    "win32_x86_64_debug"
  .         build_config=host_release:  "win32_x86_64_release"
  .
  .   * For build_config="host_debug" or "host_release" a platform specific
  .     build_dir is created by using the build_config.schema from above
  .
  . TERMINOLOGY:
  .   * CMake project directory:  Where "CMakeLists.txt" file is located.
  .   * CMake project build_dir:  Where CMake generates the build scripts for one build-configuration.
  .   * Build Configuration (build_config):
  .       - A build configuration is a named configuration data set.
  .
  . DIRECTORY STRUCTURE:
  .   WORKDIR/
  .       +-- CMAKE_PROJECT_1/                CMake project directory for "CMAKE_PROJECT_1".
  .       |     +-- build.Linux_x86_64_debug/     For build_config=host_debug on Linux (x86_64)
  .       |     +-- build.Linux_aarch64_debug/    For build_config=host_debug on Linux (aarch64)
  .       |     +-- CMakeLists.txt            CMake description for "CMAKE_PROJECT_1".
  .       |
  .       +-- CMAKE_PROJECT_2/                CMake project directory for "CMAKE_PROJECT_2".
  .
  . CMAKE-BUILD CONFIG DEFAULTS:
  .   cmake_generator: ninja
  .   cmake_toolchain: None
  .   build_dir_schema: "build.{BUILD_CONFIG}"
  .   build_config: debug


  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the CMake project "library_hello"


  @build_config.<HOST_BUILD_CONFIG_ALIAS>
  Scenario Outline: cmake-build discovers host-platform specific name for build_dir (case: build_config=<HOST_BUILD_CONFIG_ALIAS>)

    Given I use the directory "library_hello/" as working directory
    When I run "cmake-build init --build-config=<HOST_BUILD_CONFIG_ALIAS>"
    Then it should pass with:
      """
      CMAKE-INIT:  build.<EXPECTED_HOST_BUILD_CONFIG> (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=<EXPECTED_CMAKE_BUILD_TYPE> ..
      """
    And I use the CMake project "." with build_config="<EXPECTED_HOST_BUILD_CONFIG>"
    And the CMake project is initialized

    Examples:
      | HOST_BUILD_CONFIG_ALIAS | EXPECTED_HOST_BUILD_CONFIG | EXPECTED_CMAKE_BUILD_TYPE |
      | host_debug              | Windows_AMD64_debug        | Debug                     |
      | host_release            | Windows_AMD64_release      | Release                   |

