Feature: Create Packages with CPack

  As a CMake user
  I want to create binary packages in various formats
  So that the transport and installation of prebuilt artifacts is simplified

  As a CMake user
  I want to create source packages in various formats
  So that the transport and (re-)installation of source-code snapshots is simplified

  . HINT:
  .   Binary-package names and source-package names are pre-configured.
  .   The naming-scheme may differ in other CMake project examples.
  .
  . OPTION ALIASES:
  .   "--source" shorter form of "--source-bundle"

  Background: Setup CMake project workspace
    Given I use CMake project "examples/library_hello/" to setup a new working directory

  @binary_package
  Scenario Outline: Pack a binary-package in format=<Format>
    When I successfully run "cmake-build"
    When I run "cmake-build pack --format=<Format>"
    Then it should pass with:
      """
      cpack -G <Format> --config CPackConfig.cmake
      """
    And the command output should contain:
      """
      CPack: - package: {__WORKDIR__}/build.debug/libhello-0.2.1_binary.<PackageFileExtension> generated.
      """
    But note that "build-step is often required before packing a binary-package"

    Examples:
      | Format | PackageFileExtension |
      | ZIP    | zip                  |
      | TGZ    | tar.gz               |


  @source_package
  Scenario Outline: Pack a source-package in format=<Format>
    When I run "cmake-build pack --format=<Format> --source"
    Then it should pass with:
      """
      cpack -G <Format> --config CPackSourceConfig.cmake
      """
    And the command output should contain:
      """
      CPack: - package: {__WORKDIR__}/build.debug/libhello-0.2.1_source.<PackageFileExtension> generated.
      """
    But note that "source-packages must use the --source option"

    Examples:
      | Format | PackageFileExtension |
      | ZIP    | zip                  |
      | TGZ    | tar.gz               |


  @binary_package
  Scenario: Pack binary-package without options
    When I successfully run "cmake-build"
    When I run "cmake-build pack"
    Then it should pass with:
      """
      cpack -G ZIP --config CPackConfig.cmake
      """
    And the command output should contain:
      """
      CPack: - package: {__WORKDIR__}/build.debug/libhello-0.2.1_binary.zip generated.
      """
    But note that "build-step is often required before packing a binary-package"
    And note that "the default package-format may differ and depend on CMakeLists.txt"


  @source_package
  Scenario: Pack source-package without options
    When I run "cmake-build pack --source"
    Then it should pass with:
      """
      cpack -G ZIP --config CPackSourceConfig.cmake
      """
    And the command output should contain:
      """
      CPack: - package: {__WORKDIR__}/build.debug/libhello-0.2.1_source.zip generated.
      """
    But note that "the default package-format may differ and depend on CMakeLists.txt"


  Scenario: Pack with --cpack-config=CPACK-CONFIG-FILE option
    When I run "cmake-build pack --format=ZIP --cpack-config=CPackSourceConfig.cmake"
    Then it should pass with:
      """
      cpack -G ZIP --config CPackSourceConfig.cmake
      """
    And the command output should contain:
      """
      CPack: - package: {__WORKDIR__}/build.debug/libhello-0.2.1_source.zip generated.
      """

  Scenario: Pack with --package-dir=DESTDIR option (Override: CPACK_PACKAGE_DIRECTORY)
    When I successfully run "cmake-build"
    When I run "cmake-build pack --format=ZIP --package-dir=OTHER_DIR"
    Then it should pass with:
      """
      cpack -G ZIP --config CPackConfig.cmake -B {__WORKDIR__}/build.debug/OTHER_DIR
      """
    And the command output should contain:
      """
      CPack: - package: {__WORKDIR__}/build.debug/OTHER_DIR/libhello-0.2.1_binary.zip generated.
      """

  Scenario: Pack performs init (if needed)
    When I run "cmake-build pack --format=ZIP --source"
    Then it should pass with:
      """
      CMAKE-INIT:  build.debug (using cmake.generator=ninja)
      """
    And the command output should contain:
      """
      CMAKE-PACK: build.debug (using cpack.generator=ZIP)
      """

  Scenario: Pack fails if CMakeLists.txt contains no CPack support
    Given a file named "CMakeLists.txt" with:
      """
      cmake_minimum_required(VERSION 3.0)
      project(libhello VERSION 0.2.2 LANGUAGES CXX)

      add_library(hello STATIC
          src/hello/Responder.cpp
      )
      add_library(HELLO::hello ALIAS hello)
      target_include_directories(hello
          PUBLIC
              $<INSTALL_INTERFACE:include>
              $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
      )
      # -- MINIMAL-CPACK-SUPPORT:
      # MISSING: include(CPack)
      """
    But note that "the CMakeLists.txt file lacks CPack support"
    When I run "cmake-build pack --format=ZIP"
    Then it should fail with:
      """
      CPack Error: Cannot find CPack config file: "CPackConfig.cmake"
      """

