# -*- encoding: UTF-8 -*-
"""
Workhorse to build the CMake project model elements from parts.
"""

from __future__ import absolute_import, print_function
from path import Path
import six
from invoke import Exit
from cmake_build.host_platform import make_build_config_name
from cmake_build.model import (
    CMakeProject, CMakeProjectData, BuildConfig,
    CMakeProjectWithoutProjectDirectory,
    CMakeProjectWithoutCMakeListsFile
)
from cmake_build.pathutil import posixpath_normpath


# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
# pylint: disable=bad-whitespace
HOST_BUILD_CONFIG_DEBUG   = make_build_config_name(build_type="debug")
HOST_BUILD_CONFIG_RELEASE = make_build_config_name(build_type="release")
BUILD_CONFIG_DEFAULT = "debug"
BUILD_CONFIG_DEFAULT_MAP = dict(debug={}, release={})
BUILD_CONFIG_DEFAULT_MAP[BUILD_CONFIG_DEFAULT] = {}
BUILD_CONFIG_HOST_MAP = {
    HOST_BUILD_CONFIG_DEBUG: {},
    HOST_BUILD_CONFIG_RELEASE: {},
}


# pylint: enable=bad-whitespace
# -----------------------------------------------------------------------------
# BUILD CONFIG RELATED:
# -----------------------------------------------------------------------------
def make_build_config(ctx, name=None):
    if name == "host_debug" or name == "auto":
        name = HOST_BUILD_CONFIG_DEBUG
    elif name == "host_release":
        name = HOST_BUILD_CONFIG_RELEASE

    name = name or ctx.config.build_config or "default"
    build_config_defaults = CMakeProjectData().data
    build_config_defaults["cmake_generator"] = ctx.config.cmake_generator or "ninja"
    build_config_defaults["cmake_toolchain"] = ctx.config.cmake_toolchain
    build_config_defaults["cmake_build_type"] = None
    build_config_defaults["cmake_defines"] = []  # MAYBE: ctx.config.cmake_defines
    build_config_defaults["build_dir_schema"] = ctx.config.build_dir_schema
    build_config_data = {}
    build_config_data.update(build_config_defaults)
    build_config_data2 = ctx.config.build_configs_map.get(name) or {}
    build_config_data.update(build_config_data2)
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
    if strict is None:
        strict = True
    project_dirs = cmake_select_project_dirs(ctx, projects, strict=strict)
    cmake_projects = []
    for project_dir in project_dirs:
        cmake_project = make_cmake_project(ctx, project_dir, build_config,
                                           strict=strict, **kwargs)
        cmake_projects.append(cmake_project)
    return cmake_projects


def show_cmake_project_ignored_args(cmake_project_kwargs):
    if not cmake_project_kwargs:
        return

    # -- NORMAL CASE:
    for name, value in six.iteritems(cmake_project_kwargs):
        if value is None:
            continue
        print("cmake_project: IGNORED_ARGS: %s=%r" % (name, value))
