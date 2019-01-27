# -*- coding: UTF-8 -*-
# XXX-WIP
"""
Provides the command tool for command-line processing.
"""

from __future__ import absolute_import
from .command import main

# ---------------------------------------------------------------------------
# AUTO-MAIN:
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.exit(main())
