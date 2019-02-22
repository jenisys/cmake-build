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
from path import Path

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
# from invoke.exceptions import Failure
from invoke import task, Collection

# -- TASK-LIBRARY:
from .tasklet.cleanup import cleanup_tasks, config_add_cleanup_dirs
from .model_builder import (
    make_cmake_projects, make_build_configs_map, BUILD_CONFIG_DEFAULT
)
from .model import CMakeBuildRunner

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
          dry_run=False, strict=True):
    """Clean one or cmake project(s) by removing the build artifacts."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         strict=True, verbose=True)
    for cmake_project in cmake_projects:
        cmake_project.clean(args=args)     # MAYBE: dry_run=dry_run)


@task
def clean_and_ignore_failures(ctx, project="all", build_config=None, args=None,
                              dry_run=False):
    """Perform build-system clean target and ignore any failures (best-effort)."""
    clean(ctx, project=project, build_config=build_config, args=args,
          strict=False)


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
         args=None, init_args=None, test_args=None, use_test=False):
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
        if use_test:
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
cleanup_tasks.add_task(clean_and_ignore_failures, "clean_cmake-build")
cleanup_tasks.configure(namespace.configuration({}))

# -- REGISTER DEFAULT CLEANUP_DIRS (if configfile is not provided):
# HINT: build_dir_schema: build.{BUILD_CONFIG}
config_add_cleanup_dirs(["build.*"])
