XXX-CLEANUP-TODO

EXAMPLE: 10_StaticLib_example1
=============================================================================

This project provides a simple example how to build:

* one C++ static library
* source code is located in a "src/" subdirectory

::

    $ mkdir build
    $ cd build
    
    # -- BUILD-SCRIPT-VARIANT: Makefiles
    $ cmake ..
    $ make
    # USE: make clean
    
    # -- BUILD-SCRIPT-VARIANT: Ninja build scripts
    cmake -G Ninja
    ninja
    # USE: ninja clean

In ROOT directory::

    invoke cmake.build -p <THIS_DIRECTORY>
    invoke cmake.build -p <THIS_DIRECTORY> -g ninja
    invoke cmake.build -p <THIS_DIRECTORY> -g make
    invoke cmake.build      #  Build all projects w/ default cmake.generator.

    invoke cmake.clean -p <THIS_DIRECTORY>  # Cleanup this cmake project.
    invoke cmake.clean                      # Cleanup all  cmake projects.
