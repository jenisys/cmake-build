cmake-build
=============================================================================

.. _CMake: https://cmake.org
.. _`cmake-build`: https://github.com/jenisys/cmake-build

`cmake-build`_ simplifies usage of `CMake`_ by making it directly usable
as build system.

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

    # -- EXAMPLE: Specify the cmake.generator on command-line (override config-file).
    # HINT: Complicate CMake generator names (multiple words) are also available as short aliases.
    $ cmake-build --generator=ninja
    ...
    $ cmake-build --generator=make
    ...

    # -- EXAMPLE: Use multiple build_configs (or build directories) directly.
    # HINT: Simplify usage of pre-canned cross-compiles/toolchain on command-line.
    $ cmake-build --build-config=Linux_arm64_Debug
    ...
    $ cmake-build --build-config=Linux_arm64_Release --target=rebuild
    ...


Goals of `cmake-build`:

* Simplify command-line usage of `CMake`_ (one step procedure)
* Provide core configuration aspects of CMake project(s) in a configuration file
* Supports multiple **build configurations** and **toolchains**
* Can build multiple `CMake`_ projects at once


Configuration File Support
-----------------------------------------------------------------------------

File "$WORKDIR/cmake-build_config.yaml":

.. code-block:: yaml

    generator: ninja
    build_dir_schema:    "build/{BUILD_CONFIG}"
    build_config_schema: "{OSTYPE}_{CPU}_{CMAKE_BUILD_TYPE}"
    build_config_aliases:
        default: Linux_arm64_Debug
        all:
          - Linux_arm64_Debug
          - Linux_arm64_Release

    build_configs:
        # -- HOST-COMPILE BUILD-CONFIGS (normally):
        Linux_x86_64_Debug:
            cmake_defines:
              - CMAKE_BUILD_TYPE=Debug

        Linux_x86_64_Release:
            cmake_defines:
              - CMAKE_BUILD_TYPE=Release

        # -- CROSS-COMPILE BUILD-CONFIGS (normally):
        Linux_arm64_Debug:
            toolchain: cmake/toolchain/linux_gcc_arm64.cmake
            cmake_defines:
              - CMAKE_BUILD_TYPE=MinSizeDbg

        Linux_arm64_Release:
            toolchain: cmake/toolchain/linux_gcc_arm64.cmake
            cmake_defines:
              - CMAKE_BUILD_TYPE=Release

    projects:
      - examples/program_hello
      - examples/library_hello
