# -*- coding: UTF-8 -*-
"""
Workhorse to build the CMake project model elements from parts.
"""

from __future__ import absolute_import, print_function
from path import Path
from collections import OrderedDict
import os
import six
from invoke import Exit
from cmake_build.host_platform import make_build_config_name
from cmake_build.model import (
    CMakeProject, CMakeProjectWithoutProjectDirectory,
    CMakeProjectWithoutCMakeListsFile
)
from cmake_build.config import CMakeProjectConfig, BuildConfig
from cmake_build.pathutil import posixpath_normpath


# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
# pylint: disable=bad-whitespace
HOST_BUILD_CONFIG_DEBUG   = make_build_config_name(build_type="debug")
HOST_BUILD_CONFIG_RELEASE = make_build_config_name(build_type="release")
BUILD_CONFIG_DEFAULT = os.environ.get("CMAKE_BUILD_CONFIG", "debug")
BUILD_CONFIG_DEFAULT_MAP = dict(debug={}, release={})
BUILD_CONFIG_DEFAULT_MAP[BUILD_CONFIG_DEFAULT] = {}
BUILD_CONFIG_HOST_MAP = {
    HOST_BUILD_CONFIG_DEBUG: {},
    HOST_BUILD_CONFIG_RELEASE: {},
}

BUILD_CONFIGS_DEFAULT = [
    "debug",
    "release",
]
HOST_BUILD_CONFIGS_DEFAULT = [
    "host_{0}".format(name) for name in BUILD_CONFIGS_DEFAULT
]
if BUILD_CONFIG_DEFAULT.startswith("host_"):
    BUILD_CONFIGS_DEFAULT = HOST_BUILD_CONFIGS_DEFAULT

BUILD_CONFIG_ALIAS_MAP = {
    "all": BUILD_CONFIGS_DEFAULT,
    "host_all": HOST_BUILD_CONFIGS_DEFAULT,
}


# pylint: enable=bad-whitespace
# -----------------------------------------------------------------------------
# BUILD CONFIG RELATED:
# -----------------------------------------------------------------------------
# BOOLEAN_VALUE_MAP = {False: "OFF", True: "ON"}

def cmake_define_normalize(item):
    if isinstance(item, str):
        item = (item, None)
    elif isinstance(item, dict):
        assert len(item) == 1, "OOPS: %r (expected: size=1)" % item
        item = list(item.items())[0]
    elif not isinstance(item, tuple):
        raise ValueError("cmake_defines: unexpected item.type: %r" % item)

    name, value = item
    # if isinstance(value, bool):
    #    item = (name, BOOLEAN_VALUE_MAP[value])
    return item


def cmake_defines_normalize(items):
    if not items:
        return []
    elif isinstance(items, dict):
        raise ValueError("cmake_defines: isa dict (expected: list)")

    return [cmake_define_normalize(item) for item in items]

def make_build_config_defaults(config):
    cmake_defines_items0 = cmake_defines_normalize(config.cmake_defines or [])
    build_config_defaults = CMakeProjectConfig().data
    build_config_defaults["cmake_generator"] = config.cmake_generator or "ninja"
    build_config_defaults["cmake_toolchain"] = config.cmake_toolchain
    build_config_defaults["cmake_build_type"] = None
    build_config_defaults["cmake_install_prefix"] = config.cmake_install_prefix or None
    # build_config_defaults["cmake_defines"] = []  # MAYBE: ctx.config.cmake_defines
    build_config_defaults["cmake_defines"] = OrderedDict(cmake_defines_items0)
    build_config_defaults["build_dir_schema"] = config.build_dir_schema
    return build_config_defaults


def make_build_config(ctx, name=None):
    if name == "host_debug" or name == "auto":
        name = HOST_BUILD_CONFIG_DEBUG
    elif name == "host_release":
        name = HOST_BUILD_CONFIG_RELEASE

    name = name or ctx.config.build_config or "default"
    build_config_defaults = make_build_config_defaults(ctx.config)
    build_config_data = {}
    build_config_data.update(build_config_defaults)
    build_config_data2 = ctx.config.build_configs_map.get(name) or {}
    build_config_data.update(build_config_data2)

    # -- STEP: Make cmake_toolchain path relative to config_dir.
    config_dir = ctx.config.config_dir or "."
    cmake_toolchain = build_config_data.get("cmake_toolchain")
    if cmake_toolchain:
        # -- ASSUMPTION: cmake_toolchain is a relative-path.
        cmake_toolchain = Path(cmake_toolchain)
        if not cmake_toolchain.isabs():
            cmake_toolchain = Path(config_dir)/cmake_toolchain
            cmake_toolchain = cmake_toolchain.normpath()
            build_config_data["cmake_toolchain"] = cmake_toolchain

    # -- STEP: build_config.cmake_defines inherits common.cmake_defines
    cmake_defines = build_config_defaults["cmake_defines"]
    cmake_defines_items = cmake_defines_normalize(
        build_config_data2.get("cmake_defines", []))
    if cmake_defines_items:
        # -- INHERIT DEFAULT CMAKE_DEFINES (override and/or merge them):
        use_override = cmake_defines_items[0][0] == "@override"
        if use_override:
            cmake_defines = OrderedDict(cmake_defines_items)
        else:
            # -- MERGE-AND-OVERRIDE:
            # New items are added, existing items replaced/overwritten.
            cmake_defines = cmake_defines.copy()
            cmake_defines.update(OrderedDict(cmake_defines_items))

    build_config_data["cmake_defines"] = cmake_defines
    return BuildConfig(name, build_config_data)


def make_build_configs_map(build_configs):
    # build_configs_map = dict(BUILD_CONFIG_DEFAULT=dict())
    build_configs_map = BUILD_CONFIG_DEFAULT_MAP.copy()
    # DISABLED: build_configs_map.update(BUILD_CONFIG_HOST_MAP)
    for build_config in build_configs:
        if isinstance(build_config, six.string_types):
            build_configs_map[build_config] = {}
        elif isinstance(build_config, dict):
            assert len(build_config) == 1, "ENSURE: length=1 (%r)" % build_config
            name = list(build_config.keys())[0]
            build_config_data = build_config[name]
            build_configs_map[name] = build_config_data
        else:
            # pylint: disable=line-too-long
            raise ValueError("UNEXPECTED: %r (expected: string, dict(size=1)" % build_config)
    return build_configs_map


def require_build_config_is_valid(ctx, build_config, strict=True):
    if not build_config:
        build_config = ctx.config.build_config or BUILD_CONFIG_DEFAULT

    if build_config == "host_debug" or build_config == "auto":
        build_config = HOST_BUILD_CONFIG_DEBUG
    elif build_config == "host_release":
        build_config = HOST_BUILD_CONFIG_RELEASE

    build_configs = ctx.config.build_configs or []
    build_configs_map = ctx.config.get("build_configs_map", None)
    if not build_configs_map or build_configs_map == BUILD_CONFIG_DEFAULT_MAP:
        build_configs_map = make_build_configs_map(build_configs)
        ctx.config.build_configs_map = build_configs_map

    build_config_data = build_configs_map.get(build_config)
    if build_config_data is None:
        build_config_data = BUILD_CONFIG_HOST_MAP.get(build_config)
    if build_config_data is not None:
        return True

    expected = ", ".join(sorted(list(build_configs_map.keys())))
    message = "UNKNOWN BUILD-CONFIG: %s (expected: %s)" % (build_config, expected)
    if not strict:
        print(message)
        return False

    # -- STRICT MODE: Here and no further.
    raise Exit(message, code=10)
    # raise Failure(message)


def require_build_config_is_valid_or_none(ctx, build_config, strict=True):
    if not build_config or build_config == BUILD_CONFIG_DEFAULT:
        return True
    return require_build_config_is_valid(ctx, build_config, strict=strict)


# -----------------------------------------------------------------------------
# CMAKE PROJECT MODEL BUILDER RELATED:
# -----------------------------------------------------------------------------
def cmake_select_project_dirs(ctx, projects=None, strict=True):
    # pylint: disable=too-many-branches
    projects = projects or "all"
    project_dirs = []
    if isinstance(projects, six.string_types):
        if projects == "all":
            project_dirs = ctx.config.projects or []
        else:
            project_dirs = [projects]
    elif isinstance(projects, (list, tuple)):
        project_dirs = projects
    else:
        raise ValueError("projects=%r with type=%s" % (projects, type(projects)))

    if not project_dirs:
        # -- CONSIDER CURRENT_DIR: As cmake.project
        curdir = Path(".").abspath()
        curdir = posixpath_normpath(curdir)
        if Path("CMakeLists.txt").isfile():
            # pylint: disable=line-too-long
            print("CMAKE-BUILD: Using . (as default cmake.project; cwd={0})".format(curdir))
            project_dirs = [Path(".")]
        else:
            # pylint: disable=line-too-long
            print("CMAKE-BUILD: Ignore . (not a cmake.project; cwd={0})".format(curdir))


    missing_project_dirs = []
    for project_dir in project_dirs:
        project_dir = Path(project_dir)
        if not project_dir.isdir():
            missing_project_dirs.append(project_dir)
        yield project_dir

    # -- FINAL-DIAGNOSTICS: NO_PROJECT_DIRS, ...
    message = ""
    if not project_dirs:
        message = "CMAKE-BUILD: OOPS, no projects are specified (STOP HERE)."
    # -- DISABLED:
    # elif len(project_dirs) == len(missing_project_dirs):
    #     message = "CMAKE-BUILD: OOPS, all projects are MISSING."
    #     strict = False

    if message:
        if strict:
            raise Exit(message, code=10)
        else:
            print(message)


def cmake_select_build_configs(ctx, build_config):
    """Select the build_configs that should be applied.

    If the ``build_config="all"`` alias is used,
    all currently configured build_configs are returned.

    :param build_config:    Build config or build config alias to use.
    :return: List of build_config names to use.
    """
    build_configs = [build_config]
    alias_value = ctx.config.build_config_aliases.get(build_config)
    if alias_value:
        # -- EXPERIMENT: Support build_config_aliases:
        #   alias_name: sequence<name> or name (as string)
        if callable(alias_value):
            generate_names_func = alias_value
            build_configs = list(generate_names_func())
        elif isinstance(alias_value, six.string_types):
            build_configs = [alias_value]
        else:
            assert isinstance(alias_value, (list, tuple))
            build_configs = alias_value
    elif build_config == "host_all":
        build_configs = HOST_BUILD_CONFIGS_DEFAULT
    elif build_config == "all":
        # -- SPECIAL-CASE BUILD_CONFIG ALIAS: all
        # HINT: References all BUILD_CONFIGS or the DEFAULT ones.
        build_configs = ctx.config.build_configs or BUILD_CONFIGS_DEFAULT
        if isinstance(build_configs, dict):
            build_configs = list(build_config.keys())
        elif isinstance(build_configs, list):
            build_configs2 = []
            for build_config2 in build_configs:
                if not build_config2:
                    continue

                if isinstance(build_config2, dict):
                    # -- CASE: List of dicts with size=1.
                    assert len(build_config2) == 1
                    build_config2 = list(build_config2.keys())[0]
                else:
                    # -- CASE: Only build_config name is used (as string).
                    assert isinstance(build_config2, six.string_types), \
                           "REQUIRE-STRING: %r" % build_config
                build_configs2.append(build_config2)
            build_configs = build_configs2
    return build_configs


def make_cmake_project(ctx, project_dir, build_config=None, strict=False, **kwargs):
    if not ctx.config.build_configs_map:
        # -- LAZY-INIT: Build build_configs_map once from build_configs list.
        build_configs_map = make_build_configs_map(ctx.config.build_configs)
        ctx.config.build_configs_map = build_configs_map
        # MAYBE-MORE:
        # CMakeBuildConfigNormalizer.normalize(ctx.config)

    cmake_generator = kwargs.pop("generator", None)
    build_config_default = ctx.config.build_config or BUILD_CONFIG_DEFAULT
    build_config = build_config or build_config_default
    require_build_config_is_valid_or_none(ctx, build_config, strict=strict)

    # -- CREATE CMAKE PROJECT:
    # HINT: Detect SPECIAL CASES with FAULT SYNDROMES first.
    project_dir = Path(project_dir)
    cmake_list_file = project_dir/"CMakeLists.txt"
    if not project_dir.isdir():
        cmake_project = CMakeProjectWithoutProjectDirectory(project_dir)
    elif not cmake_list_file.isfile():
        cmake_project = CMakeProjectWithoutCMakeListsFile(project_dir)
    else:
        # -- NORMAL CASE:
        build_config_obj = make_build_config(ctx, build_config)
        cmake_project = CMakeProject(ctx, project_dir,
                                     build_config=build_config_obj,
                                     cmake_generator=cmake_generator)
        show_cmake_project_ignored_args(kwargs)
    return cmake_project


def make_cmake_projects(ctx, projects, build_config=None, strict=None, **kwargs):
    """Create CMake projects from project and build_config combinations.

    .. hint::

        A build_config may represent a list of build_configs.
        EXAMPLE: "all", "host_all"

    :param ctx: Invoke task context to use
    :param projects:     List of CMake projects to use.
    :param build_config: Build config or build_config alias to use.
    :param strict:
    :return: List of CMake project objects.
    """
    if strict is None:
        strict = True
    project_dirs = list(cmake_select_project_dirs(ctx, projects, strict=strict))
    build_configs = cmake_select_build_configs(ctx, build_config)

    cmake_projects = []
    for _build_config in build_configs:
        for project_dir in project_dirs:
            cmake_project = make_cmake_project(ctx, project_dir, _build_config,
                                               strict=strict, **kwargs)
            cmake_projects.append(cmake_project)
    return cmake_projects


def show_cmake_project_ignored_args(cmake_project_kwargs):
    if not cmake_project_kwargs:
        return

    # -- NORMAL CASE:
    for name, value in six.iteritems(cmake_project_kwargs):
        if value is None or not value:
            continue
        print("cmake_project: IGNORED_ARGS: %s=%r" % (name, value))
