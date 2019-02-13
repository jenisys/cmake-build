# *- coding: UTF-8 -*-
"""
Host platforrm specific parts.
"""

from __future__ import absolute_import
import platform


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
BUILD_CONFIG_SCHEMA = "{SYSTEM}_{PROCESSOR}_{BUILD_TYPE}"
BUILD_TYPE = "debug"


# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------
def uname_system():
    """system/OS name, like: Darwin, Linux, win32"""
    # -- OR: os.uname()
    parts = platform.uname()
    return parts[0]


def uname_processor():
    parts = platform.uname()
    return parts[4]     # ACTUALLY: machine


def make_build_config_name(build_type=None, schema=None, **kwargs):
    """Build the BUILD_CONFIG name for the current host platform
    (with a discoverable schema).

    :param build_type:  CMAKE_BUILD_TYPE name to use (like: Debug, ...)
    :param schema:      Name schema to use (format-style placeholders).
    :param kwargs:      Addition keywords args.
    :return: BUILD_CONFIG name to use (normally for the HOST platform).
    """
    build_type = build_type or BUILD_TYPE
    schema = schema or BUILD_CONFIG_SCHEMA
    os_name = kwargs.pop("SYSTEM", None) or uname_system()
    processor = kwargs.pop("PROCESSOR", None) or uname_processor()
    if "CPU" not in kwargs:
        # -- ALIAS FOR: PROCESSOR
        kwargs["CPU"] = uname_processor()
    build_config_name = schema.format(SYSTEM=os_name,
                                      PROCESSOR=processor,
                                      BUILD_TYPE=build_type,
                                      **kwargs)
    return build_config_name
