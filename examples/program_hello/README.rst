EXAMPLE: program_hello
=============================================================================

This project provides a simple example how to build one C++ program.
Build steps:

* Builds ../library_hello (co-located)
* Builds program_hello

::

    $ cmake-build
    ...     # Performs CMake init, then builds the CMake project (and runs the tests)

    $ cmake-build build --build-config=release
    ...     # Init/builds the CMake project with build-config=release

    $ cmake-build cleanup
    ...     # Remove CMake build-dir(s).

Run example program (manually)::

    $ build.debug/hello_app
    Hello Alice

    $ build.debug/hello_app Bob and Charly
    Hello Bob and Charly


