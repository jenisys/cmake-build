# -*- coding: UTF-8 -*-
# XXX-WIP
"""
Provides the command tool for command-line processing.
"""

from __future__ import absolute_import
import sys
from .command import cmake_build
# from .command import main

# ---------------------------------------------------------------------------
# AUTO-MAIN:
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cmake_build(auto_envvar_prefix="CMAKE_BUILD")
