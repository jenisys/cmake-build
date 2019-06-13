EXAMPLE: library_hello
=============================================================================

This project provides a simple example how to build:

* one C++ static library
* source code is located in a "src/" subdirectory
* simple test source code is located under "test/" subdirectory

::

    $ cmake-build
    ...     # Performs CMake init, then builds the CMake project (and runs the tests)

    $ cmake-build build --build-config=release
    ...     # Init/builds the CMake project with build-config=release

    $ cmake-build cleanup
    ...     # Remove CMake build-dir(s).
