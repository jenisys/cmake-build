# -*- coding: UTF-8 -*-
# pylint: disable=wrong-import-position, wrong-import-order
# pylint: disable=unused-argument, redefined-builtin
"""
Invoke tasks for building C/C++ projects w/ CMake.

.. code-block:: YAML

    # -- FILE: invoke.yaml
    cmake:
        generator: ninja
        project_dirs:
          - 01_Program_example1
          - 01_Program_example2
          - CTEST_example1

.. seealso::

    * https://cmake.org
"""

from __future__ import absolute_import, print_function
from cmake_build.pathutil import posixpath_normpath
import six
from path import Path

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
# from invoke.exceptions import Failure
from invoke import task, Collection
from invoke.exceptions import Failure, Exit

# -- TASK-LIBRARY:
from .tasklet.cleanup import cleanup_tasks, config_add_cleanup_dirs
from .model import CMakeProject, CMakeProjectData, CMakeBuildRunner, BuildConfig
from .host_platform import make_build_config_name


# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
HOST_BUILD_CONFIG_DEBUG   = make_build_config_name(build_type="debug")
HOST_BUILD_CONFIG_RELEASE = make_build_config_name(build_type="release")
BUILD_CONFIG_DEFAULT = "debug"
BUILD_CONFIG_DEFAULT_MAP = dict(debug={}, release={})
BUILD_CONFIG_DEFAULT_MAP[BUILD_CONFIG_DEFAULT] = {}
BUILD_CONFIG_HOST_MAP = {
    HOST_BUILD_CONFIG_DEBUG: {},
    HOST_BUILD_CONFIG_RELEASE: {},
}


# -----------------------------------------------------------------------------
# TASK UTILITIES:
# -----------------------------------------------------------------------------
# CHECK-IF-REALLY-NEEDED:
# class CMakeBuildConfigNormalizer(object):
#
#     @staticmethod
#     def normalize_build_configs(config):
#         build_configs = config.build_configs
#         if isinstance(build_configs, (list, tuple)):
#             # -- CASE: Convert build_configs as list into dict.
#             the_build_configs = {}
#             for build_config in build_configs:
#                 the_build_configs[build_config] = {}
#             config.build_configs = the_build_configs
#
#     @classmethod
#     def normalize(cls, config):
#         # DISABLED: cls.normalize_build_configs(config)
#         pass

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
    raise Exit(message)
    # raise Failure(message)


def require_build_config_is_valid_or_none(ctx, build_config, strict=True):
    if not build_config or build_config == BUILD_CONFIG_DEFAULT:
        return True
    return require_build_config_is_valid(ctx, build_config, strict=strict)


def cmake_select_project_dirs(ctx, projects=None, strict=True, verbose=False):
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
        curdir = Path(".").abspath()
        if Path("CMakeLists.txt").isfile():
            print("CMAKE-BUILD: Using . (as default cmake.project; cwd={0})".format(curdir))
            project_dirs = [Path(".")]
        else:
            print("CMAKE-BUILD: Ignore . (not a cmake.project; cwd={0})".format(curdir))

    missing_project_dirs = []
    for project_dir in project_dirs:
        project_dir = Path(project_dir)
        if not project_dir.isdir():
            if verbose:
                print("CMAKE-BUILD: Skip project {0} (NOT-FOUND)".format(
                    posixpath_normpath(project_dir)))
                missing_project_dirs.append(project_dir)
            continue
        yield project_dir

    # -- FINALLY:
    if len(missing_project_dirs) == len(project_dirs):
        if missing_project_dirs:
            # -- OOPS: Only missing project_dirs
            message = "CMAKE-BUILD: OOPS, all projects are MISSING (STOP HERE)."
            # print(message)
        else:
            message = "CMAKE-BUILD: OOPS, no projects are specified (STOP HERE)."
            # print(message)
        if strict:
            raise Exit(message)
            # raise Failure(message)
        else:
            print(message)


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


def show_cmake_project_ignored_args(cmake_project_kwargs):
    if not cmake_project_kwargs:
        return

    # -- NORMAL CASE:
    for name, value in six.iteritems(cmake_project_kwargs):
        if value is None:
            continue
        print("cmake_project: IGNORED_ARGS: %s=%r" % (name, value))


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

    build_config = make_build_config(ctx, build_config)
    cmake_project = CMakeProject(ctx, project_dir, build_config=build_config,
                                 cmake_generator=cmake_generator)
    show_cmake_project_ignored_args(kwargs)
    return cmake_project


def make_cmake_projects(ctx, projects, build_config=None, strict=None,
                        verbose=True, **kwargs):
    if strict is None:
        strict = True
    project_dirs = cmake_select_project_dirs(ctx, projects,
                                             strict=strict,
                                             verbose=verbose)
    cmake_projects = []
    for project_dir in project_dirs:
        cmake_project = make_cmake_project(ctx, project_dir, build_config,
                                           strict=strict, **kwargs)
        cmake_projects.append(cmake_project)
    return cmake_projects


# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
TASK_ARGS_HELP_MAP = {
    "project": 'Project directory or "all" (for all projects) (as path)',
    "build-config": "Build configuration to use: debug, release, ... (as string)",
    "generator": "cmake.generator to use: ninja, make, ... (as string)",
    "args": "Arguments to pass (as string)",
}
TASK_ARGS_HELP_MAP_WITH_INIT_ARGS = {
    "init-args": "CMake args to use to initialize the build_dir."
}
TASK_ARGS_HELP_MAP_WITH_INIT_ARGS.update(TASK_ARGS_HELP_MAP)


@task(help=TASK_ARGS_HELP_MAP)
def init(ctx, project="all", build_config=None, generator=None, args=None):
    """Initialize one or all cmake project(s).
    This means that the project build_dir is created and the build scripts
    are generated with CMake for this build configuration.
    """
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.init(args=args)


@task(help=TASK_ARGS_HELP_MAP_WITH_INIT_ARGS)
def build(ctx, project="all", build_config=None, generator=None,
          args=None, init_args=None):
    """Build one or all cmake project(s)."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.build(args=args, init_args=init_args)


@task(aliases=["ctest"],
      help=TASK_ARGS_HELP_MAP_WITH_INIT_ARGS)
def test(ctx, project="all", build_config=None, generator=None,
         args=None, init_args=None):
    """Test one or all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.test(args=args, init_args=init_args)


@task(help=TASK_ARGS_HELP_MAP)
def clean(ctx, project="all", build_config=None, args=None,
          dry_run=False):
    """Clean one or cmake project(s) by removing the build artifacts."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         strict=False, verbose=False)
    for cmake_project in cmake_projects:
        cmake_project.clean(args=args)     # MAYBE: dry_run=dry_run)


@task(help=TASK_ARGS_HELP_MAP)
def reinit(ctx, project="all", build_config=None, generator=None, args=None,
           dry_run=False):
    """Reinit cmake projects (performs: cleanup, init)."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         init_args=args, verbose=False)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.reinit(args=args)    # PREPARED, TODO: dry_run=dry_run)


@task(help=TASK_ARGS_HELP_MAP_WITH_INIT_ARGS)
def rebuild(ctx, project="all", build_config=None, generator=None,
            args=None, init_args=None):
    """Rebuild one or all cmake projects (performs: clean, build)."""
    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         verbose=False)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.rebuild(args=args, init_args=init_args)
    # PREPARED, TODO: dry_run=dry_run)


# @task(name="all")
# def build_all(ctx, project="all", generator=None, build_config=None,
#         args=None, init_args=None, test_args=None):
#     """Performs multiple stsps for one (or more) projects:
#
#     - cmake.init
#     - cmake.build
#     - cmake.test (= ctest)
#     """
#     cmake_projects = make_cmake_projects(ctx, project,
#                                          build_config=build_config,
#                                          init_args=args,
#                                          verbose=False)
#     for cmake_project in cmake_projects:
#         cmake_project.build(args=args, init_args=init_args)
#         cmake_project.test(args=test_args)

@task(help=TASK_ARGS_HELP_MAP_WITH_INIT_ARGS)
def redo(ctx, project="all", build_config=None, generator=None,
         args=None, init_args=None, test_args=None):
    """Performs multiple steps for one (or more) project(s).

    Steps:

    - cmake.reinit
    - cmake.build
    - cmake.test (= ctest)
    """
    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator,
                                         init_args=args)
    for cmake_project in cmake_projects:
        cmake_project.reinit(args=init_args)
        cmake_project.build(args=args)
        cmake_project.test(args=test_args)


def cmake_build_show_projects(projects):
    print("PROJECTS[%d]:" % len(projects))
    for project in projects:
        project = Path(project)
        annotation = ""
        if not project.isdir():
            annotation = "NOT-EXISTS"
        print("  - {project} {note}".format(project=project, note=annotation))


def cmake_build_show_build_configs(build_configs):
    print("BUILD_CONFIGS[%d]:" % len(build_configs))
    for build_config in build_configs:
        print("  - {build_config}".format(build_config=build_config))


@task
def config(ctx):
    """Show cmake-build configuration details."""
    from pprint import pprint
    # config = ctx.config
    if not ctx.config.build_configs_map:
        build_configs_map = make_build_configs_map(ctx.config.build_configs)
        ctx.config.build_configs_map = build_configs_map

    print("cmake_generator: %s" % ctx.config.cmake_generator)
    cmake_build_show_build_configs(ctx.config.build_configs)
    cmake_build_show_projects(ctx.config.projects)
    pprint(ctx.config, indent=4)
    print("-------------------------")
    pprint(dict(ctx.config), indent=4)


# -----------------------------------------------------------------------------
# TASK CONFIGURATION:
# -----------------------------------------------------------------------------
namespace = Collection(redo, init, test, clean, reinit, rebuild, config)
namespace.add_task(build, default=True)
# DISABLED: namespace.add_task(build_all)

TASKS_CONFIG_DEFAULTS = {
    "cmake_generator": None,
    "cmake_toolchain": None,
    "build_dir_schema": "build.{BUILD_CONFIG}",
    "build_config": BUILD_CONFIG_DEFAULT,
    "build_configs": [],
    "build_configs_map": {},    # -- AVOID-HERE: BUILD_CONFIG_DEFAULT_MAP.copy(),
    "projects": [],
}
namespace.configure(TASKS_CONFIG_DEFAULTS)
namespace.configuration({})

# -- REGISTER CLEANUP TASKS:
cleanup_tasks.add_task(clean, "clean_cmake-build")
cleanup_tasks.configure(namespace.configuration({}))

# -- REGISTER DEFAULT CLEANUP_DIRS (if configfile is not provided):
# HINT: build_dir_schema: build.{BUILD_CONFIG}
config_add_cleanup_dirs(["build.*"])
