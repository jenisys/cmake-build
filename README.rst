cmake-build
=============================================================================

.. _CMake: https://cmake.org
.. _`cmake-build`: https://github.com/jenisys/cmake-build

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

    # -- EXAMPLE: Specify the cmake.generator on command-line (override config-file).
    # HINT: Complicated CMake generator names (multiple words) are also available as short aliases.
    $ cmake-build build --generator=ninja
    ...
    $ cmake-build build --generator=make
    ...

    # -- EXAMPLE: Use multiple build_configs (or build directories) directly.
    # HINT: Simplify usage of pre-canned cross-compiles/toolchain on command-line.
    $ cmake-build --build-config=Linux_arm64_Debug
    ...
    $ cmake-build rebuild --build-config=Linux_arm64_Release
    ...


Goals of `cmake-build`:

* Simplify command-line usage of `CMake`_ (one step procedure)
* Provide core configuration aspects of CMake project(s) in a configuration file
* Supports multiple **build configurations** and **toolchains**
* Can build multiple `CMake`_ projects at once


Configuration File Support
-----------------------------------------------------------------------------

File "$WORKDIR/cmake_build.yaml":

.. code-block:: yaml

    cmake_generator: ninja              #< DEFAULT cmake.generator.
    build_dir_schema: "build.{BUILD_CONFIG}"
    build_config: Linux_arm64_Debug     #< DEFAULT build_config.
    build_configs:
        # -- HOST-COMPILE BUILD-CONFIGS (example):
        # HINT: AUTO-DISCOVERED with build_config=host_debug, host_release
        - Linux_x86_64_Debug:
            # cmake_build_type: Debug

        - Linux_x86_64_Release:
            cmake_build_type: MinSizeRel

        # -- CROSS-COMPILE BUILD-CONFIGS (example):
        - Linux_arm64_Debug:
            cmake_toolchain:  cmake/toolchain/linux_gcc_arm64.cmake
            cmake_build_type: MinSizeDbg
            cmake_defines:
              - FOO=foo

        - Linux_arm64_Release:
            cmake_toolchain:  cmake/toolchain/linux_gcc_arm64.cmake
            cmake_build_type: MinSizeRel

    projects:
      - examples/program_hello
      - examples/library_hello
