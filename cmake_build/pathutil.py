# -*- coding -*-
"""
Provides some utility functions for path.

TODO:
  matcher that ignores empty lines and whitespace and has contains comparison
"""

from __future__ import absolute_import
import os.path
from path import Path


# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS:
# -----------------------------------------------------------------------------
def posixpath_normpath(pathname):
    """
    Convert path into POSIX path:

      * Normalize path
      * Replace backslash with slash

    :param pathname: Pathname (as string)
    :return: Normalized POSIX path.
    """
    backslash = "\\"
    pathname2 = os.path.normpath(pathname) or "."
    if backslash in pathname2:
        pathname2 = pathname2.replace(backslash, "/")
    return Path(pathname2)
