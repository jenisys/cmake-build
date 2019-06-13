EXAMPLES: CMake Projects
=============================================================================

This project provides a simple example how to use "cmake-build"
with 2 CMake projects:

* library_hello (simple static-library)
* program_hello (simple program, uses library_hello)

Usage examples::

    $ cmake-build
    ...     # Performs CMake init, then builds the CMake project (and runs the tests)

    $ cmake-build build --build-config=release
    ...     # Init/builds the CMake project with build-config=release

    $ cmake-build cleanup
    ...     # Remove CMake build-dir(s).

