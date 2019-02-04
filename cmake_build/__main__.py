# -*- coding: UTF-8 -*-
# XXX-WIP
"""
Provides the command tool for command-line processing.
"""

from __future__ import absolute_import
import sys
from cmake_build.program import program
# from .command import main

# ---------------------------------------------------------------------------
# AUTO-MAIN:
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(program.run())
