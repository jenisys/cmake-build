Feature: cmake-build clean Command

  As a cmake build user
  I want remove any build artifacts
  So that I can perform a clean build
  (or to make a clean source code archive afterwards).

  . HINT:
  .   The "cmake-build clean" delegates cleanup to the generated build-script.
  .   The CMake project build_dir remains intact (if it pre-existed).
  .   The CMake project is not initialized for the current build-config.

  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the directory "library_hello/" as working directory
    And I use the CMake project "."


  Scenario: CMake Project (build dir) is initialized (Perform: clean)
    When I successfully run "cmake-build init"
    Then the CMake project is initialized for build_config="debug"
    But note that "INTERESTING PART starts here"
    When I run "cmake-build clean"
    Then it should pass with:
      """
      CMAKE-INIT:  build.debug (SKIPPED: Initialized with cmake.generator=ninja).
      CMAKE-CLEAN: build.debug
      """
    And the command output should contain:
      """
      cmake --build . -- clean
      """
    And the CMake project is initialized for build_config="debug"

  Scenario: CMake Project (build dir) is not initialized (Skip: clean)
    Then the CMake project is not initialized for build_config="debug"
    When I run "cmake-build clean"
    Then it should pass with:
      """
      CMAKE-CLEAN: build.debug (SKIPPED: not initialized yet)
      """
    And the directory "build.debug" should not exist
    And the CMake project is not initialized for build_config="debug"


  Scenario: CMake Project (build dir) exists and is initialized but is broken (Perform: clean and fail)
    When I successfully run "cmake-build init"
    Then the CMake project is initialized for build_config="debug"
    When I remove the file "build.debug/build.ninja"
    But note that "INTERESTING PART starts here"
    When I run "cmake-build clean"
    Then it should fail with:
      """
      ninja: error: loading 'build.ninja': No such file or directory
      """
    And the command output should contain:
      """
      cmake --build . -- clean
      """

  Scenario: CMake Project (build dir) is not created yet (Skip: clean)
    Given the directory "build.debug" does not exist
    When I run "cmake-build clean"
    Then it should pass with:
      """
      CMAKE-CLEAN: build.debug (SKIPPED: not initialized yet)
      """


  Scenario: CMake Project (directory) has no "CMakeLists.txt" file (Fail: clean)
    Given I remove the file "CMakeLists.txt"
    When I run "cmake-build clean"
    Then it should fail with:
      """
      CMAKE-BUILD: Ignore . (not a cmake.project; cwd={__WORKDIR__})
      CMAKE-BUILD: OOPS, no projects are specified (STOP HERE).
      """


  Scenario: CMake Project (directory) does not exist (Fail: clean)
    Given the directory "UNKNOWN_DIR" should not exist
    When I run "cmake-build clean --project=UNKWOWN_DIR"
    Then it should pass with:
      """
      CMAKE-CLEAN: UNKWOWN_DIR (SKIPPED: cmake.project directory does not exist)
      """
    But note that "the missing cmake.project directory is gracefully ignored"
