EXAMPLE: program_hello
=============================================================================

This project provides a simple example how to build one C++ program.

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

    $ ./hello_app
    Hello Alice

    $ ./hello_app Bob and Charly
    Hello Bob and Charly


