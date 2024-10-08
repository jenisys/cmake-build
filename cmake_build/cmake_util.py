# -*- coding: UTF-8 -*-
"""
This module contains utility functions to simplify usage of `CMake`_.

.. _CMake: https://cmake.org/
"""

from __future__ import absolute_import, print_function
import os
from collections import OrderedDict
from path import Path
import six

from cmake_build._path import monkeypatch_path_if_needed
monkeypatch_path_if_needed()


# -----------------------------------------------------------------------------
# CMAKE PROJECT CONFIGURATION:
# -----------------------------------------------------------------------------
# Generators
#
# The following generators are available on this platform:
#   Unix Makefiles               = Generates standard UNIX makefiles.
#   Ninja                        = Generates build.ninja files.
#   Ninja Multi-Config           = Generates build-<Config>.ninja files.
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
    "ninja.multi":  "Ninja Multi-Config",
    "ninja-multi":  "Ninja Multi-Config",
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
CPACK_GENERATOR = os.environ.get("CPACK_GENERATOR",
                  os.environ.get("CMAKE_BUILD_PACK_FORMAT", "ZIP"))


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


class CMakeDefine(object):

    def __init__(self, name=None, value=None, type=None):
        self.name = name
        self.value = value
        self.type = type

    def __str__(self):
        value = self.value
        if value is None:
            value = "ON"
        elif isinstance(value, bool):
            value = CMAKE_BOOLEAN_VALUE_MAP[value]

        if self.type:
            return "{name}:{type}={value}".format(
                name=self.name, type=self.type, value=value)
        else:
            return "{name}={value}".format(name=self.name, value=value)

    def as_tuple(self):
        if self.type:
            return (self.name, self.value, self.type)
        else:
            return (self.name, self.value)

    def as_option_string(self):
        return "-D{0}".format(self)

    @classmethod
    def from_tuple(cls, data):
        assert 2 <= len(data) <= 3
        if len(data) >= 3:
            return cls(data[0], data[1], data[2])
        else:
            return cls(data[0], data[1])

    @classmethod
    def parse(cls, text):
        text = text.strip()
        if "=" not in text:
            raise ValueError("INVALID CMAKE-DEFINE: %s (expected: NAME=VALUE)" % text)

        type = None
        parts = text.split("=", 1)
        name = parts[0]
        if ":" in parts[0]:
            name, type = parts[0].split(":", 1)
        if len(parts) >= 2:
            assert len(parts) == 2
            value = parts[1]
        return cls(name=name, value=value, type=type)

    @classmethod
    def parse_many(cls, text_list):
        return [cls.parse(text) for text in text_list]



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
        generator_schema = '-G {0}'
        needs_quoting = cmake_generator.count(" ") > 0
        if needs_quoting:
            # -- CASE: Generator name w/ multiple words => QUOTE it.
            generator_schema = '-G "{0}"'
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
    """Builds CMake define options for the command-line,
    like: ``-DCMAKE_TOOLCHAIN_FILE=toolchain.cmake``

    :param defines:     CMake defines (list, dict, OrderedDict).
    :param generator:   CMAKE_GENERATOR to use (if any).
    :param toolchain:   CMAKE_TOOLCHAIN_FILE to use (if any).
    :param build_type:  CMAKE_BUILD_TYPE to use (if any).
    :param install_prefex:  CMAKE_INSTALL_PREFIX to use (if any).
    :param named_defines:   Additional CMake defines (name=value, ...).
    :return: CMake define options (as string; BAD SHOULD BE: list).
    """
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
            item = "-D{0}=ON".format(name)
        define_options.append(item)
    return " ".join(define_options)


def cmake_cmdline_options(args=None, defines=None, generator=None,
                  toolchain=None, build_type=None, config=None,
                  install_prefix=None, **named_defines):
    """Build CMake command-line options (as list) from the parts.

    :param args:        CMake arguments to use (list<string>, string).
    :param defines:     CMake defines (list, dict, OrderedDict).
    :param generator:   CMAKE_GENERATOR to use (if any).
    :param toolchain:   CMAKE_TOOLCHAIN_FILE to use (if any).
    :param build_type:  CMAKE_BUILD_TYPE to use (if any).
    :param config:      CONFIG to use (cmake --config <CONFIG> option).
    :param install_prefex:  CMAKE_INSTALL_PREFIX to use (if any).
    :param named_defines:   Additional CMake defines (name=value, ...).
    :return: CMake command-line options (as list).
    """
    if defines is None:
        defines = []
    elif isinstance(defines, (dict, OrderedDict)):
        defines = defines.items()

    build_type = config or build_type
    options =[]
    if generator:
        options.append(cmake_cmdline_generator_option(generator))
    if config:
        # -- SUPPORT MULTI-CONFIGURATION GENERATORS:
        options.append("--config {0}".format(config))

    if defines or toolchain or build_type or install_prefix:
        cmake_define_options = cmake_cmdline_define_options(defines,
                                                toolchain=toolchain,
                                                build_type=build_type,
                                                install_prefix=install_prefix)
        if isinstance(cmake_define_options, six.string_types):
            # -- BAD: Normally returned as string
            options.append(cmake_define_options)
        else:
            options.extend(cmake_define_options)
    if args:
        if isinstance(args, (list, tuple)):
            options.extend(args)
        else:
            options.append(args)
    return options


def cmake_cmdline(args=None, defines=None, generator=None,
                  toolchain=None, build_type=None, config=None,
                  install_prefix=None, **named_defines):
    """Build a CMake command-line from the parts

    :param args:        CMake arguments to use (list<string>, string).
    :param defines:     CMake defines (list, dict, OrderedDict).
    :param generator:   CMAKE_GENERATOR to use (if any).
    :param toolchain:   CMAKE_TOOLCHAIN_FILE to use (if any).
    :param build_type:  CMAKE_BUILD_TYPE to use (if any).
    :param config:      CONFIG to use (cmake --config <CONFIG> option).
    :param install_prefex:  CMAKE_INSTALL_PREFIX to use (if any).
    :param named_defines:   Additional CMake defines (name=value, ...).
    :return: CMake command-line (as string).
    """
    cmake_options = cmake_cmdline_options(args=args,
                            defines=defines, generator=generator,
                            toolchain=toolchain,
                            build_type=build_type, config=config,
                            install_prefix=install_prefix, **named_defines)
    cmdline = " ".join(cmake_options)
    return cmdline.strip()
