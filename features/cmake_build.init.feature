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
  .   * CMake project directory:  Where "CMakeLists.txt" file is located.
  .   * CMake project build_dir:  Where CMake generates the build scripts for one build-configuration.
  .   * Build Configuration (build_config):
  .       - A build configuration is a named configuration data set.
  .       - A build configuration contains all the data to setup a CMake project.
  .       - A build configuration may inherit parts of its data (from other config areas).
  .       - A project has normally multiple build configurations (like: debug, release)
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
  . CMAKE-BUILD CONFIG DEFAULTS:
  .   cmake_generator: ninja
  .   cmake_toolchain: None
  .   build_dir_schema: "build.{BUILD_CONFIG}"
  .   build_config: debug


  Background: Setup CMake Workspace
    Given a new working directory
    And a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        build_configs:
          - debug
          - release

        projects:
          - library_hello
        """
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the CMake project "library_hello"

  Scenario: CMake Project build_dir does not exist (perform: init)
    When I run "cmake-build init"
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

  Scenario: CMake Project build_dir exists and is initialized (skip: init)
    When I run "cmake-build init"
    Then the CMake project is initialized
    But note that "INTERESTING PART: Run 'cmake-build init' again"
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-INIT:  library_hello/build.debug (SKIPPED: Initialized with cmake.generator=ninja)
      """
    And the command output should not contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the command output should not contain:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.debug
      """

  Scenario: CMake Project build_dir exists but is not initialized (perform: reinit)
    Given I ensure that the directory "library_hello/build.debug" exists
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-INIT:  library_hello/build.debug (NEEDS-REINIT)
      CMAKE-INIT:  library_hello/build.debug (using cmake.generator=ninja)
      """
    And the CMake project is initialized
    And the command output should contain:
      """
      cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the command output should contain:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.debug
      """

    Scenario: CMake Project is initialized and should use another cmake.generator (perform: reinit)
    When I run "cmake-build init"
    Then the CMake project is initialized
    But note that "INTERESTING PART: Run 'cmake-build init' again"
    When I run "cmake-build init --generator=make"
    Then it should pass with:
      """
      CMAKE-INIT:  library_hello/build.debug (NEEDS-REINIT)
      CMAKE-INIT:  library_hello/build.debug (using cmake.generator=make)
      """
    And the command output should contain:
      """
      cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Debug ..
      """
    And the command output should contain:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.debug
      """

  Scenario: CMake Project directory does not exist (skip-and-fail)
    Given I remove the directory "library_hello/"
    When I run "cmake-build init"
    Then it should fail with:
      """
      CMAKE-INIT: library_hello (SKIPPED: cmake.project directory does not exist)
      """
    And the command output should not contain:
      """
      CMAKE-INIT:  library_hello/build.debug
      """
    And the command output should not contain "cmake -G"

  Scenario: CMake Project is initialized but configfile.build_config data differs (perform: update; cmake_build_type)
    When I run "cmake-build init"
    Then the CMake project is initialized
    But note that "INTERESTING PART: Starts here"
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        build_configs:
          - debug:
              cmake_build_type: OTHER

        projects:
          - library_hello
        """
    But note that "CHANGED: cmake_build_type=OTHER (was: Debug)"
    When I run "cmake-build init --clean-config"
    Then it should pass with:
      """
      CMAKE-INIT:  library_hello/build.debug (NEEDS-UPDATE, using cmake.generator=ninja)
      CMAKE-CONFIGURE: library_hello/build.debug
      """
    And the command output should contain:
      """
      cmake -DCMAKE_BUILD_TYPE=OTHER ..
      """
    And the command output should contain:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.debug
      """

  Scenario: CMake Project is initialized but configfile.build_config data differs (perform: update; cmake_defines)
    When I run "cmake-build init"
    Then the CMake project is initialized
    But note that "INTERESTING PART: Starts here"
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        build_configs:
          - debug:
              cmake_build_type: Debug
              cmake_defines:
                - NEW_PARAM: foo

        projects:
          - library_hello
        """
    But note that "CHANGED: cmake_defines=... (was: EMPTY)"
    When I run "cmake-build init --clean-config"
    Then it should pass with:
      """
      CMAKE-INIT:  library_hello/build.debug (NEEDS-UPDATE, using cmake.generator=ninja)
      CMAKE-CONFIGURE: library_hello/build.debug
      """
    And the command output should contain:
      """
      cmake -DCMAKE_BUILD_TYPE=Debug -DNEW_PARAM=foo ..
      """
    And the command output should contain:
      """
      -- Build files have been written to: {__WORKDIR__}/library_hello/build.debug
      """

  Scenario: CMake Project stored cmake.generator is preferred over configfile (skip: reinit)

    INTENTION: Simplify usage of other cmake.generators (on command-line)
    without need to change the configfile:cmake_generator (cmake.generator default value).

    When I run "cmake-build init --generator=make"
    Then the CMake project is initialized
    And the command output should contain:
      """
      CMAKE-INIT:  library_hello/build.debug (using cmake.generator=make)
      """
    And note that "configfile: cmake_generator=ninja (DIFFERS)"
    But note that "INTERESTING PART: Run 'cmake-build init' again without generator"
    When I run "cmake-build init"
    Then it should pass with:
      """
      CMAKE-INIT:  library_hello/build.debug (SKIPPED: Initialized with cmake.generator=make)
      """
    But note that "the stored cmake.generator is preserved/used"

  Scenario: cmake-build configfile does not contain any projects (fail)
    Given a file named "cmake_build.yaml" with:
        """
        cmake_generator: ninja
        build_configs:
          - debug:
              cmake_build_type: Debug
        """
    But note that "NO PROJECTS are specified in configfile"
    When I run "cmake-build init"
    Then it should fail with:
      """
      CMAKE-BUILD: OOPS, no projects are specified (STOP HERE).
      """
    But note that "this is no problem if a CMakeLists.txt file exists"
