Feature: cmake-build init Command

  As a cmake build user
  I want to initialize a CMake project to create its build directory only if needed
  So that it always works independent of its initial state.

  . DESIGN RULES:
  .   * CMAKE_PROJECT BUILD_DIR does not exist yet for this BUILD_CONFIG:
  .     Initialize the CMake project build dir with the build_config data.
  .
  .   * CMAKE_PROJECT BUILD_DIR exists and has SAME BUILD_CONFIG DATA:
  .     Do nothing if the CMake project build dir is initialized
  .     and the build_config data has not changed.
  .
  .   * CMAKE_PROJECT BUILD_DIR exists and has OTHER BUILD_CONFIG DATA:
  .     Reinitialize the CMake project build dir for this build_config.
  .
  . TERMINOLOGY:
  .   * BUILD_CONFIG:
  .       - A project has normally multiple build configurations (like: debug, release)
  .       - A build configuration is a named configuration data set.
  .       - A build configuration contains all the data to setup a CMake project.
  .       - A build configuration may inherit parts of its data (from other config areas).
  .       - May specify a CMAKE_BUILD_TYPE (as: cmake_build_type).
  .       - May specify a CMake toolchain file (for cross-compiling).
  .
  . DIRECTORY STRUCTURE:
  .   WORKDIR/
  .       +-- cmake_build.yaml                cmake-build configuration file.
  .       +-- CMAKE_PROJECT_1/                CMake project directory for "CMAKE_PROJECT_1".
  .       |     +-- build.debug/              CMake project build_dir for build_config=debug
  .       |     +-- build.release/            CMake project build_dir for build_config=release
  .       |     +-- build.Linux_arm64_debug/  CMake project build_dir for build_config=Linux_arm64_debug
  .       |     +-- CMakeLists.txt            CMake description for "CMAKE_PROJECT_1".
  .       |
  .       +-- CMAKE_PROJECT_2/                CMake project directory for "CMAKE_PROJECT_2".
  .

  Background: Setup CMake Workspace
    Given a new working directory
    And a file named "cmake_build.yaml" with:
        """
        # build_dir_schema: "build.{BUILD_CONFIG}"
        # build_config_aliases:
        #   default: debug

        cmake_generator: ninja
        build_configs:
          debug:
            cmake_build_type: Debug
          release:
            cmake_build_type: MinSizeRel

        projects:
          - library_hello
        """
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the CMake project "library_hello"

  Scenario: CMake Project (build dir) does not exist (perform: init)
    When I run "cmake-build init --build-config=debug"
    Then it should pass with:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.debug
      """
    And the command output should contain:
      """
      CMAKE-INIT:  library_hello/build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the CMake project is initialized
    But note that "the following steps verify the initialized project build_dir state"
    And the directory "library_hello/build.debug" exists
    And a file named "library_hello/build.debug/.cmake_build.build_config.json" exists


  Scenario: CMake Project (build dir) exists but is not initialized (perform: init before build)
  Scenario: CMake Project (build dir) exists and is initialized (skip: init before build)
  Scenario: CMake Project (build dir) is initialized and should use another cmake.generator (perform: init before build)
  Scenario: CMake Project (directory) does not exist (skip: cmake_project)
