Feature: cmake-build build Command

  As a cmake build user
  I want to use CMake as (macro) build system without need
  to manually initialize the build system (by generating it with CMake)
  So that I directly build independent of the CMake project's initialized state.
  (and I do need to remember the parameters or do the manual steps).

  Background: Setup CMake Workspace


  Scenario: CMake Project (build dir) does not exist (perform: init before build)
  Scenario: CMake Project (build dir) exists but is not initialized (perform: init before build)
  Scenario: CMake Project (build dir) exists and is initialized (skip: init before build)
  Scenario: CMake Project (build dir) is initialized and should use another cmake.generator (perform: init before build)
  Scenario: CMake Project (directory) does not exist (skip: cmake_project)
