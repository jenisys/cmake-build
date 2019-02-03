Feature: cmake-build clean Command

  As a cmake build user
  I want remove any build artifacts
  So that I can perform a clean build
  (or to make a clean source code archive afterwards).

  Background: Setup CMake Workspace


  Scenario: CMake Project (build dir) is initialized (Perform: clean)
  Scenario: CMake Project (build dir) is not initialized (Skip: clean)
  Scenario: CMake Project (build dir) is not created yet (Skip: clean)
  Scenario: CMake Project (directory) does not exist (Skip: clean)
