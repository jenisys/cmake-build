Feature: cmake-build cleanup Command

  As a cmake build user
  I want remove any CMake build directories and build artifacts
  So that I reach a clean workspace state again
  (and I can create a clean source code archive afterwards).

  HINT: Cleans up any build_dir from any build_config (matching: cleanup.directories patterns).


  Background: Setup CMake Workspace
    Given a new working directory
    And I copy the directory "examples/cmake/" to the working directory
    And I copy the CMake project "examples/library_hello/" to the working directory
    And I use the directory "library_hello/" as working directory
    And I use the CMake project "."


  Scenario: CMake Project (build dir) is initialized (Perform: cleanup)
    When I successfully run "cmake-build init"
    Then the CMake project is initialized for build_config="debug"
    But note that "INTERESTING PART starts here"
    When I run "cmake-build cleanup"
    Then it should pass with:
      """
      CLEANUP TASK: clean-cmake-build
      CMAKE-BUILD: Using . (as default cmake.project; cwd={__WORKDIR__})
      CMAKE-INIT:  build.debug (SKIPPED: Initialized with cmake.generator=ninja).
      CMAKE-CLEAN: build.debug
      """
    And the command output should contain:
      """
      RMTREE: build.debug
      """
    And the directory "build.debug" should not exist

  Scenario: CMake Project (build dir) exists but is not initialized (Perform: cleanup)
    Given I ensure that the directory "build.debug" exists
    Then the CMake project is not initialized for build_config="debug"
    When I run "cmake-build cleanup"
    Then it should pass with:
      """
      CMAKE-CLEAN: build.debug (SKIPPED: not initialized yet)
      RMTREE: build.debug
      """
    And the directory "build.debug" should not exist

  Scenario: CMake Project (build dir) exists and is initialized but is broken (Perform: cleanup)
    When I successfully run "cmake-build init"
    Then the CMake project is initialized for build_config="debug"
    When I remove the file "build.debug/build.ninja"
    But note that "INTERESTING PART starts here"
    When I run "cmake-build cleanup"
    Then it should pass with:
      """
      FAILURE in CLEANUP TASK: clean-cmake-build (GRACEFULLY-IGNORED)
      CLEANUP TASKS: 1 failures occured
      RMTREE: build.debug

      ninja: error: loading 'build.ninja': No such file or directory
      """
    And the directory "build.debug" should not exist

  Scenario: CMake Project (build dir) is not created yet (Skip: cleanup)
    Given the directory "build.debug" does not exist
    When I run "cmake-build cleanup"
    Then it should pass with:
      """
      CMAKE-CLEAN: build.debug (SKIPPED: not initialized yet)
      """
    And the command output should not contain "RMTREE: build.debug"


  Scenario: CMake Project (directory) has no "CMakeLists.txt" file (Perform: cleanup if needed)
    Given I remove the file "CMakeLists.txt"
    And I ensure that the directory "build.debug" exists
    And I ensure that the directory "build.release" exists
    When I run "cmake-build cleanup"
    Then it should pass with:
      """
      CMAKE-BUILD: Ignore . (not a cmake.project; cwd={__WORKDIR__})
      CMAKE-BUILD: OOPS, no projects are specified (STOP HERE).
      RMTREE: build.debug
      RMTREE: build.release
      """
    And note that "the directories build.* are cleaned up anyway"
    But note that "not a cmake.project is GRACEFULLY IGNORED"


  Scenario: CMake Project (directory) does not exist (Skip: cleanup)
    Given the directory "UNKNOWN_DIR" should not exist
    And   a file named "cmake_build.yaml" with:
      """
      projects:
        - UNKWOWN_DIR
      """
    When I run "cmake-build cleanup"
    Then it should pass with:
      """
      CLEANUP TASK: clean-cmake-build
      """
    But note that "cmake-build clean task does not perform anything"
    And note that "the non-existing UNKNOWN_DIR is silently ignored"
