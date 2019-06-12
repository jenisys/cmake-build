# -*- coding: UTF-8 -*-
"""
This module contains utility functions to simplify usage of `CMake`_.

.. _CMake: https://cmake.org/
"""

from __future__ import absolute_import, print_function
from collections import OrderedDict
from path import Path
import six


# -----------------------------------------------------------------------------
# CMAKE PROJECT CONFIGURATION:
# -----------------------------------------------------------------------------
# Generators
#
# The following generators are available on this platform:
#   Unix Makefiles               = Generates standard UNIX makefiles.
#   Ninja                        = Generates build.ninja files.
#   Xcode                        = Generate Xcode project files.
#   CodeBlocks - Ninja           = Generates CodeBlocks project files.
#   CodeBlocks - Unix Makefiles  = Generates CodeBlocks project files.
#   CodeLite - Ninja             = Generates CodeLite project files.
#   CodeLite - Unix Makefiles    = Generates CodeLite project files.
#   Sublime Text 2 - Ninja       = Generates Sublime Text 2 project files.
#   Sublime Text 2 - Unix Makefiles
#                                = Generates Sublime Text 2 project files.
#   Kate - Ninja                 = Generates Kate project files.
#   Kate - Unix Makefiles        = Generates Kate project files.
#   Eclipse CDT4 - Ninja         = Generates Eclipse CDT 4.0 project files.
#   Eclipse CDT4 - Unix Makefiles= Generates Eclipse CDT 4.0 project files.
#
# BUILD_DIR = "build"
BUILD_DIR_SCHEMA = "build.{BUILD_CONFIG}"
BUILD_CONFIG_DEFAULT = "default"

CMAKE_DEFAULT_GENERATOR = "ninja"  # EMPTY means Makefiles ('Unix Makefiles')
CMAKE_GENERATOR_ALIAS_MAP = {
    "ninja":    "Ninja",
    "make":     "Unix Makefiles",
    "xcode":    "Xcode",
    "CodeBlocks":       "CodeBlocks - Ninja",
    "CodeBlocks.ninja": "CodeBlocks - Ninja",
    "CodeBlocks.make":  "CodeBlocks - Unix Makefiles",
    "CodeLite":         "CodeLite - Ninja",
    "CodeLite.ninja":   "CodeLite - Ninja",
    "CodeLite.make":    "CodeLite - Unix Makefiles",
    "eclipse":          "Eclipse CDT4 - Ninja",
    "eclipse.ninja":    "Eclipse CDT4 - Ninja",
    "eclipse.make":     "Eclipse CDT4 - Unix Makefiles",
    "kate":             "Kate - Ninja",
    "kate.ninja":       "Kate - Ninja",
    "kate.make":        "Kate - Unix Makefiles",
    "sublime2":         "Sublime Text 2 - Ninja",
    "sublime2.ninja":   "Sublime Text 2 - Ninja",
    "sublime2.make":    "Sublime Text 2 - Unix Makefiles",
}

CMAKE_BUILD_TYPES = [
    "Debug", "Release", "RelWithDebInfo", "MinSizeRel"
]

CMAKE_BOOLEAN_VALUE_MAP = {False: "OFF", True: "ON"}


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


def cmake_cmdline_generator_option(generator):
    generator_option = ""
    if generator:
        cmake_generator = CMAKE_GENERATOR_ALIAS_MAP.get(generator) or generator
        generator_schema = '-G {0} '
        needs_quoting = cmake_generator.count(" ") > 0
        if needs_quoting:
            # -- CASE: Generator name w/ multiple words => QUOTE it.
            generator_schema = '-G "{0}" '
        generator_option = generator_schema.format(cmake_generator)
    return generator_option


def cmake_cmdline_toolchain_option(toolchain):
    if not toolchain:
        return ""
    # -- OTHERWISE
    return "-DCMAKE_TOOLCHAIN_FILE={0}".format(Path(toolchain).abspath())


def cmake_normalize_defines(defines):
    # -- NORMALIZE-DEFINES:
    if isinstance(defines, OrderedDict):
        defines = defines.items()

    defines2 = []
    for d in defines:
        if isinstance(d, tuple):
            assert len(d) == 2
            pass
        elif isinstance(d, dict):
            assert len(d) == 1, "ENSURE: d.size=%d: %r" % (len(d), d)
            d = list(d.items())[0]
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


# def cmake_cmdline_define_options(defines, toolchain=None, build_type=None,
#                                  install_prefix=None, **kwargs):
#     defines2 = cmake_normalize_defines(defines or [])
#     defines = []
#     # print("cmake_defines1: %r" % defines)
#
#     # parts = [
#     #     ("CMAKE_BUILD_TYPE", build_type),
#     #     ("CMAKE_INSTALL_PREFIX", install_prefix),
#     # ]
#     # builder = CMakeCmdlineBuilder4Defines(defines)
#     # if toolchain:
#     #     builder.add("CMAKE_TOOLCHAIN_FILE", Path(toolchain).abspath())
#     # for name, value in parts:
#     #     if value:
#     #         builder.add((name, value))
#
#     if toolchain:
#         cmake_defines_add(defines, "CMAKE_TOOLCHAIN_FILE", Path(toolchain).abspath())
#     if build_type:
#         cmake_defines_add(defines, "CMAKE_BUILD_TYPE", build_type)
#     if install_prefix:
#         cmake_defines_add(defines, "CMAKE_INSTALL_PREFIX", install_prefix)
#     if kwargs:
#         for name, value in six.iteritems(kwargs):
#             cmake_defines_add(name, value)
#     defines.extend(defines2)
#     if not defines:
#         return ""
#
#     define_options = []
#     # print("cmake_defines2: %r" % defines)
#     for name, value in defines:
#         if value is not None:
#             item = "-D{0}={1}".format(name, value)
#         else:
#             item = "-D{0}".format(name)
#         define_options.append(item)
#     return " ".join(define_options)

def cmake_cmdline_define_options(defines, toolchain=None, build_type=None,
                                 install_prefix=None, **kwargs):
    # print("XXX defines= %r" % defines)
    cmake_defines0 = OrderedDict(cmake_normalize_defines(defines or []))
    cmake_defines = OrderedDict()

    if toolchain:
        toolchain = Path(toolchain).abspath()

    # -- STEP: Use precious defines first (ensure: ordering)
    precious_defines = [
        ("CMAKE_TOOLCHAIN_FILE", toolchain),
        ("CMAKE_BUILD_TYPE", build_type),
        ("CMAKE_INSTALL_PREFIX", install_prefix),
    ]
    for name, value in precious_defines:
        other_value = None
        if name in cmake_defines0:
            # -- ENSURE: Item is removed.
            other_value = cmake_defines0.pop(name)
        if value is None:
            # -- CASE: Use optional default as cmake_define
            value = other_value
        if value is None:
            continue
        cmake_defines[name] = value
        assert name not in cmake_defines0

    # -- STEP: Add remaining cmake_defines
    cmake_defines.update(cmake_defines0)
    cmake_defines.update(kwargs)
    if not cmake_defines:
        return ""

    define_options = []
    for name, value in cmake_defines.items():
        if value is not None:
            if isinstance(value, bool):
                # -- BOOL: Convert to OFF (False) or ON (True)
                value = CMAKE_BOOLEAN_VALUE_MAP[value]
            item = "-D{0}={1}".format(name, value)
        else:
            item = "-D{0}".format(name)
        define_options.append(item)
    return " ".join(define_options)


def cmake_cmdline(args=None, defines=None, generator=None,
                  toolchain=None, build_type=None, install_prefix=None,
                  **named_defines):
    """Build a CMake command-line from the parts"""
    if args is None:
        args = ""
    if defines is None:
        defines = []
    elif isinstance(defines, (dict, OrderedDict)):
        defines = defines.items()

    generator_part = cmake_cmdline_generator_option(generator)
    defines_part = cmake_cmdline_define_options(defines,
                                                toolchain=toolchain,
                                                build_type=build_type,
                                                install_prefix=install_prefix)
    if not isinstance(args, six.string_types):
        args = " ".join([six.text_type(x) for x in args])

    cmdline = "{generator}{defines} {args}".format(generator=generator_part,
                                                   defines=defines_part,
                                                   args=args)
    return cmdline.strip()
