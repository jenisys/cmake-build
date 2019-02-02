# -*- coding: UTF-8 -*-
"""
This module contains utility functions to simplify usage of `CMake`_.

.. _CMake: https://cmake.org/
"""

from __future__ import absolute_import, print_function
from path import Path
import six


# -----------------------------------------------------------------------------
# CMAKE PROJECT CONFIGURATION:
# -----------------------------------------------------------------------------
# BUILD_DIR = "build"
BUILD_DIR_SCHEMA = "build.{BUILD_CONFIG}"
BUILD_CONFIG_DEFAULT = "default"

CMAKE_DEFAULT_GENERATOR = "ninja"  # EMPTY means Makefiles ('Unix Makefiles')
CMAKE_GENERATOR_ALIAS_MAP = {
    "ninja": "Ninja",
    "make": "Unix Makefiles",
    "xcode": "Xcode",
    "eclipse.ninja": "Eclipse CDT4 - Ninja",
    "eclipse.make":  "Eclipse CDT4 - Unix Makefiles",
}

CMAKE_BUILD_TYPES = [
    "Debug", "Release", "RelWithDebInfo", "MinSizeRel"
]


# -----------------------------------------------------------------------------
# CMAKE UTILS:
# -----------------------------------------------------------------------------
def map_build_config_to_cmake_build_type(build_config_name):
    name = build_config_name
    cmake_build_type = None
    for build_type in CMAKE_BUILD_TYPES:
        build_type2 = build_type.lower()
        if (build_type in name) or (build_type2 in name):
            cmake_build_type = build_type
            break
    return cmake_build_type


# -----------------------------------------------------------------------------
# CMAKE CMDLINE UTILS:
# -----------------------------------------------------------------------------
def make_build_dir_from_schema(config, build_config_name):
    build_dir_schema = config.build_dir_schema or BUILD_DIR_SCHEMA
    build_dir = build_dir_schema.format(BUILD_CONFIG=build_config_name)
    return build_dir


def cmake_defines_add(cmake_defines, name, value=None):
    if value is None:
        # -- ASSUME: Boolean flag
        value = "ON"

    done = False
    for index, item in enumerate(cmake_defines):
        item_name = item[0]
        if name == item_name:
            # -- CASE: Parameter is PRE-DEFINED (override it).
            cmake_defines[index] = (name, value)
            done = True
            break

    if not done:
        # -- CASE: Parameter is UNDEFINED (up to now).
        cmake_defines.append((name, value))
    return cmake_defines


def cmake_defines_remove(cmake_defines, name):
    for index, item in enumerate(cmake_defines):
        item_name = item[0]
        if item_name == name:
            del cmake_defines[index]
            return cmake_defines
    # -- NO-CHANGE:
    return cmake_defines


def cmake_cmdline_generator_option(generator):
    generator_option = ""
    if generator:
        cmake_generator = CMAKE_GENERATOR_ALIAS_MAP.get(generator) or generator
        generator_schema = "-G {0} "
        if cmake_generator.count(" ") > 0:
            # -- CASE: Generator name w/ multiple words => QUOTE it.
            generator_schema = "-G '{0}' "
        generator_option = generator_schema.format(cmake_generator)
    return generator_option


def cmake_cmdline_toolchain_option(toolchain):
    if not toolchain:
        return ""
    # -- OTHERWISE
    return "-DCMAKE_TOOLCHAIN_FILE={0}".format(Path(toolchain).abspath())


def cmake_normalize_defines(defines):
    # -- NORMALIZE-DEFINES:
    defines2 = []
    for d in defines:
        if isinstance(d, dict):
            assert len(d) == 1, "ENSURE: d.size=%d: %r" % (len(d), d)
            d = d.items()[0]
            assert len(d) == 2, "OOPS: %r (size=%d)" % (d, len(d))
        elif isinstance(d, six.string_types):
            parts = d.split("=", 1)
            if len(parts) == 1:
                parts.append(None)
            assert len(parts) == 2, "OOPS: %r" % parts
            d = (parts[0], parts[1])
            assert len(d) == 2, "OOPS: %r (size=%d)" % (d, len(d))
        defines2.append(d)
    return defines2


def cmake_cmdline_defines_option(defines, toolchain=None, build_type=None, **kwargs):
    defines2 = cmake_normalize_defines(defines or [])
    defines = []
    # print("cmake_defines1: %r" % defines)

    if toolchain:
        cmake_defines_add(defines, "CMAKE_TOOLCHAIN_FILE", Path(toolchain).abspath())
    if build_type:
        cmake_defines_add(defines, "CMAKE_BUILD_TYPE", build_type)
    if kwargs:
        for name, value in six.iteritems(kwargs):
            cmake_defines_add(name, value)
    defines.extend(defines2)
    if not defines:
        return ""

    define_options = []
    # print("cmake_defines2: %r" % defines)
    for name, value in defines:
        if value is not None:
            item = "-D{0}={1}".format(name, value)
        else:
            item = "-D{0}".format(name)
        define_options.append(item)
    return " ".join(define_options)


def cmake_cmdline(args=None, defines=None, generator=None,
                  toolchain=None, build_type=None):
    """Build a CMake command-line from the parts"""
    if args is None:
        args = ""
    if defines is None:
        defines = []

    generator_part = cmake_cmdline_generator_option(generator)
    defines_part = cmake_cmdline_defines_option(defines,
                                                toolchain=toolchain,
                                                build_type=build_type)
    if not isinstance(args, six.string_types):
        args = " ".join([six.text_type(x) for x in args])

    cmdline = "{generator}{defines} {args}".format(generator=generator_part,
                                                   defines=defines_part,
                                                   args=args)
    return cmdline.strip()


