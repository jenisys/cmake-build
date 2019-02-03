# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os.path

# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
HERE = os.path.dirname(__file__)
TOP  = os.path.join(HERE, "../../..")
TOPA = os.path.abspath(TOP)

TOPDIR = os.environ.get("TOPDIR", None)
if not TOPDIR:
    TOPDIR = TOPA

TOP  = os.path.relpath(TOPDIR)
TOPA = TOPDIR
