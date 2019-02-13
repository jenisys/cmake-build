# *- coding: UTF-8 -*-
"""
Host platforrm specific parts.
"""

from __future__ import absolute_import
import platform
import sys


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------
BUILD_CONFIG_SCHEMA = "{SYSTEM}_{CPU}_{BUILD_TYPE}"
BUILD_TYPE = "debug"


# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------
def cmake_system():
    """Host system/OS name, like: Darwin, Linux, Windows/win32"""
    # -- OR: os.uname()
    # parts = platform.uname()
    # return parts[0]
    system_name = platform.system()
    if system_name == "Java":
        system_name = sys.platform  # Values: linux, win32, darwin, ...
    return system_name


def cmake_processor():
    """Host processor (or CPU) name."""
    # -- TOO GENERIC: processor_name = platform.processor()
    processor_name = platform.processor()
    if not processor_name:
        processor_name = cmake_machine()
    return processor_name


def cmake_machine():
    """Host processor (or CPU) name."""
    # -- TOO GENERIC: processor_name = platform.processor()
    processor_name = platform.machine()
    return processor_name


def make_build_config_name(build_type=None, schema=None, **kwargs):
    """Build the BUILD_CONFIG name for the current host platform
    (with a discoverable schema).

    Auto-discovered placeholders (on host platform):

    * SYSTEM: Operating system name, like Linux, Windows, Darwin, ...
    * PROCESSOR:  processor type (uname --processor)
    * CPU:        processor machine, architecture (uname --machine)

    :param build_type:  CMAKE_BUILD_TYPE name to use (like: Debug, ...)
    :param schema:      Name schema to use (format-style placeholders).
    :param kwargs:      Addition keywords args.
    :return: BUILD_CONFIG name to use (normally for the HOST platform).
    """
    build_type = build_type or BUILD_TYPE
    schema = schema or BUILD_CONFIG_SCHEMA
    os_name = kwargs.pop("SYSTEM", None) or cmake_system()
    processor = kwargs.pop("PROCESSOR", None) or cmake_processor()
    if "CPU" not in kwargs:
        # -- ALIAS FOR: PROCESSOR
        kwargs["CPU"] = cmake_machine()
    build_config_name = schema.format(SYSTEM=os_name,
                                      PROCESSOR=processor,
                                      BUILD_TYPE=build_type,
                                      **kwargs)
    return build_config_name
