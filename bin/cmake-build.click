#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Provides the command tool for command-line processing.
"""

from __future__ import absolute_import
# -- ENSURE: Use local path during development.
import sys
import os.path


# ----------------------------------------------------------------------------
# SETUP PATHS:
# ----------------------------------------------------------------------------
NAME = "cmake_build"
HERE = os.path.dirname(__file__)
TOP  = os.path.join(HERE, "..")
if os.path.isdir(os.path.join(TOP, NAME)):
    sys.path.insert(0, os.path.abspath(TOP))

# ----------------------------------------------------------------------------
# NORMAL PART:
# ----------------------------------------------------------------------------
from cmake_build.command import cmake_build as cmake_build_main

# ---------------------------------------------------------------------------
# AUTO-MAIN:
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(cmake_build_main(auto_envvar_prefix="CMAKE_BUILD"))
