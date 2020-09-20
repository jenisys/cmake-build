@smoke
Feature: CMake Project exists (NORMAL CASE)

  As a cmake-build user
  I want that all cmake-build commands work in principle for a CMake project
  So here is a quickcheck that makes sure of it.

  Background: Setup CMake Workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory
    And I set the environment variable "CMAKE_BUILD_CONFIG" to "release"

  Scenario Outline: Use CMake project with "cmake-build <Command>" <Variant>
    When I run "cmake-build <PreCommand> <Command> <Options>"
    Then it should pass with
      """
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      """
    And the command output should contain:
      """
      <MarkerText>
      """

    Examples:
      | Command | PreCommand | Options                  | MarkerText | Variant |
      | init    |         |                             | Build files have been written to: {__WORKDIR__}/build.release | |
      | reinit  |         |                             | Build files have been written to: {__WORKDIR__}/build.release | |
      | build   |         |                             | Linking CXX static library lib/libhello.a | |
      | rebuild |         |                             | Linking CXX static library lib/libhello.a | |
      | test    | build   |                             | 100% tests passed | |
      | clean   | init    |                             | Cleaning all built files... | |
      | update  | init    | -D CMAKE_INSTALL_PREFIX=xxx | CMAKE-UPDATE: build.release | |
      | install |         | --prefix=$PWD/.installed    | build.release/.installed/lib/libhello.a | |
      | pack    |         | --source                    | build.release/libhello-0.2.1_source.zip generated. | (SourceBundle) |
      | pack    | build   |                             | build.release/libhello-0.2.1_binary.zip generated. | (BinaryBundle) |
