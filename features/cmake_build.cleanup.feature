Feature: cmake-build cleanup Command

  As a cmake build user
  I want remove any CMake build directories and build artifacts
  So that I reach a clean workspace state again
  (and I can create a clean source code archive afterwards).

  Background: Setup CMake Workspace


  Scenario: CMake Project (build dir) is initialized (Perform: cleanup)
  Scenario: CMake Project (build dir) exists but is not initialized (Perform: cleanup)
  Scenario: CMake Project (build dir) is not created yet (Skip: cleanup)
  Scenario: CMake Project (directory) does not exist (Skip: cleanup)
