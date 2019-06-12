cmake-build
=============================================================================

.. _CMake: https://cmake.org
.. _`cmake-build`: https://github.com/jenisys/cmake-build
.. _`ninja-build`: https://ninja-build.org

`cmake-build`_ simplifies the usage of `CMake`_ by making it directly usable
as a build system.

`CMake`_ is:

* a build script generator (mostly used for C/C++ builds)
* a meta build-system for many platforms
* supports many build systems, like:
  `ninja`_, makefiles, Eclipse CDT build system, VisualStudio solutions, ...

The normal usage of `CMake` is:

.. code-block:: sh

    # -- STEP 1 (cmake.init):
    #    Initialize the build system and generate the build scripts.
    $ mkdir build && cd build/
    $ cmake -G Ninja ..
    ...

    # -- STEP 2 (cmake.build): Build something.
    $ cmake --build .
    ...

`cmake-build`_ simplifies this 2-step procedure by making it a one step procedure.
The first is automatically execute if it is needed.

.. code-block:: sh

    $ cmake-build
    ...     # Init CMake project (if needed), then builds CMake project.


`cmake-build`_ supports the following commands:

.. code-block:: sh

    $ cmake-build build
    ...     # Same as above (needed if command-line options are used).

    $ cmake-build rebuild
    ...     # Perform steps: clean, build

    $ cmake-build init
    ...     # Explicetly intializes the CMake project build-dir.

    $ cmake-build reinit
    ...     # Remove the CMake project build-dir, then performs init again.

    $ cmake-build install
    ...     # Install build artifacts to CMAKE_INSTALL_PREFIX

    $ cmake-build clean
    ...     # Remove any build artifacts by using the build system.

    $ cmake-build cleanup
    $ cmake-build cleanup.all
    ...     # Remove CMake project build-dir(s), too.

    # -- HINT: Command examples above use the default build_config (or: CMAKE_BUILD_CONFIG=debug)


.. code-block:: sh

    # -- EXAMPLE: Specify the cmake.generator on command-line (override config-file).
    # HINT: Complicated CMake generator names (multiple words) are also available as short aliases.
    $ cmake-build build --generator=ninja
    ...
    $ cmake-build build --generator=make
    ...

.. code-block:: sh

    # -- EXAMPLE: Use multiple build_configs (or build directories) directly.
    # HINT: Simplify usage of pre-canned cross-compiles/toolchain on command-line.
    $ cmake-build build --build-config=Linux_arm64_Debug
    ...

    # Using the build system, perform: clean and build with this build-config
    $ cmake-build rebuild --build-config=Linux_arm64_Release
    ...

    # -- EXAMPLE: build-config=host_debug auto-discovers the build config.
    $ cmake-build build --build-config=host_debug
    ...     # Determines build_config=Linux_x86_64_debug (for example)


Goals of `cmake-build`:

* Simplify command-line usage of `CMake`_ (one step procedure)
* Provide core configuration aspects of CMake project(s) in a configuration file
* Supports multiple **build configurations** and **toolchains**
* Can build multiple `CMake`_ projects at once


Configuration File Support
-----------------------------------------------------------------------------

File "$WORKDIR/cmake_build.yaml":

.. code-block:: yaml

    # -- FILE: cmake_build.yaml
    cmake_generator: ninja                     # Default cmake.generator.
    cmake_install_prefix: /opt/{BUILD_CONFIG}  # Default CMAKE_INSTALL_PREFIX for all build_configs.
    cmake_defines:                             # Default CMake defines for all build_configs.
      - BUILD_TESTING: off

    build_dir_schema: "build.{BUILD_CONFIG}"
    build_config: Linux_arm64_Debug     #< DEFAULT build_config.
    build_configs:
        # -- HOST-COMPILE BUILD-CONFIGS (example):
        # HINT: AUTO-DISCOVERED with build_config=host_debug, host_release
        - Linux_x86_64_Debug
            # HINT: Auto-discover cmake_build_type=Debug (CMAKE_BUILD_TYPE)

        - Linux_x86_64_Release:
            cmake_build_type: MinSizeRel

        # -- CROSS-COMPILE BUILD-CONFIGS (example):
        - Linux_arm64_Debug:
            cmake_toolchain:  cmake/toolchain/linux_gcc_arm64.cmake
            cmake_build_type: MinSizeDbg
            cmake_defines:
              - FOO: foo
              - BAR=bar     # Alternative style for a CMake define.

        - Linux_arm64_Release:
            cmake_toolchain:  cmake/toolchain/linux_gcc_arm64.cmake
            cmake_build_type: MinSizeRel
            cmake_install_prefix: /opt/Linux_arm64


    # -- OPTIONAL: Specify list of CMake project dirs (where CMakeLists.txt files are).
    projects:
      - examples/program_hello
      - examples/library_hello


    # -- CLEANUP PATTERNS: Used by "cmake-build cleanup" command.
    cleanup:
        extra_directories:
          - "examples/program_hello/build.*"
          - "build"

        extra_files:
          - **/*.log
          - **/*.bak

    # -- CLEANUP PATTERNS: Used by "cmake-build cleanup.all" command.
    cleanup_all:
        extra_directories:
          - "**/build.*"
