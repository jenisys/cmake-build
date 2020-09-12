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
from collections import OrderedDict
from path import Path


# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
# from invoke.exceptions import Failure
from invoke import task, Collection
from invoke.exceptions import Exit

# -- TASK-LIBRARY:
from .tasklet.cleanup import cleanup_tasks, config_add_cleanup_dirs
from .model_builder import (
    make_cmake_projects, make_build_configs_map, BUILD_CONFIG_DEFAULT
)
from .model import CMakeBuildRunner
from .cmake_util import CPACK_GENERATOR


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
TASK_HELP4PARAM_PROJECT = "CMake project directory (as path)"
TASK_HELP4PARAM_BUILD_CONFIG = "Build config to use: debug, release, ... (as string)"
TASK_HELP4PARAM_GENERATOR = "cmake.generator to use: ninja, make, ... (as string)"
TASK_HELP4PARAM_DEFINE = "CMake define to use: NAME=VALUE (many)"
TASK_HELP4PARAM_INIT_ARG = "CMake init arg to use (many)"
TASK_HELP4PARAM_ARG = "CMake build arg to use (many)"


@task(iterable=["define", "arg"], help={
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
    "arg": TASK_HELP4PARAM_INIT_ARG,
    "define": TASK_HELP4PARAM_DEFINE,
    "clean-config": "Remove stored_config before init (optional)",
})
def init(ctx, project="all", build_config=None, generator=None,
         arg=None, define=None,
         clean_config=False):
    """Initialize cmake project(s) (generate: build-scripts).

    POSTCONDITION:
     * cmake_project build_dir exists (is created if necessary)
     * cmake_project build-scripts are generated/updated with existing config.
    """
    cmake_defines = define or []
    cmake_init_args = arg or []
    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        if clean_config:
            # -- ENSURE:
            # Use clean cmake_project.config based on build_config data.
            cmake_project.remove_stored_config()
            cmake_project.reset_config()

        if cmake_defines:
            cmake_project.config.add_cmake_defines(cmake_defines)
        cmake_project.init(args=cmake_init_args)


@task(iterable=["arg", "opt", "init_arg", "define"], help={
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
    "arg": TASK_HELP4PARAM_ARG,
    "opt": "CMake build option to use (many)",
    "init-arg": TASK_HELP4PARAM_INIT_ARG,
    "define": TASK_HELP4PARAM_DEFINE,
    "target": "CMake build target to use (optional)",
    "jobs": "CMAKE_PARALLEL value (as int)",
    "clean-first": "Use clean-first before build (optional)",
    "verbose": "Use CMake build verbose mode (optional)",
})
def build(ctx,
          project="all", build_config=None, generator=None,
          arg=None, opt=None, init_arg=None, define=None,
          target=None, jobs=-1, clean_first=False, verbose=False):
    """Build cmake project(s)."""
    # -- HINT: Invoke default tasks needs default values for iterable params.
    cmake_build_args = arg or []
    cmake_build_options = opt or []
    cmake_init_args = init_arg or []
    cmake_defines = define or []

    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        if cmake_defines:
            cmake_project.config.add_cmake_defines(cmake_defines)
        cmake_project.build(args=cmake_build_args,
                            options=cmake_build_options,
                            init_args=cmake_init_args,
                            target=target,
                            parallel=jobs,
                            clean_first=clean_first,
                            verbose=verbose)


@task(aliases=["ctest"], iterable=["arg", "init_arg"], help={
    "arg": "CMake test arg (optional, many)",
    "init-arg": TASK_HELP4PARAM_INIT_ARG,
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
    "verbose": "Use verbose mode (optional)",
    # -- CTEST SPECIFIC OPTIONS:
    "repeat": "Repeat tests (until-pass:n, until-fail:n, after-timeout:n).",
    "rerun-failed": "Rerun failed tests.",
    "output-log": "Use --output-log=<FILE>",
    "output-on-failure": "Show test output when failure(s) occur.",
    "stop-on-failure":   "Stop test-run when failure(s) occur.",
    "progress": "Show progress.",
    "jobs": "Number of jobs (as int, CMAKE_PARALLEL).",
})
def test(ctx, project="all", build_config=None, generator=None,
         arg=None, init_arg=None, verbose=False,
         # -- CTEST SPECIFIC:
         repeat=None, rerun_failed=False,
         output_log=None, progress=False,
         output_on_failure=False, stop_on_failure=False, jobs=0):
    """Test cmake projects (performs: ctest)."""
    ctest_args = arg or []
    cmake_init_args = init_arg or []
    # -- CTEST OPTIONS:
    if repeat:
        ctest_args.append("--repeat {0}".format(repeat))
    if rerun_failed:
        ctest_args.append("--rerun-failed")
    if output_on_failure:
        # -- RELATED: CTEST_OUTPUT_ON_FAILURE (environment variable)
        ctest_args.append("--output-on-failure")
    if stop_on_failure:
        ctest_args.append("--stop-on-failure")
    if progress:
        ctest_args.append("--progress")
    if output_log:
        ctest_args.append("--output-log {0}".format(output_log))
    if jobs:
        ctest_args.append("--parallel {0}".format(jobs))

    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.test(args=ctest_args,
                           init_args=cmake_init_args,
                           verbose=verbose)


@task(help={
    "prefix": "CMAKE_INSTALL_PREFIX to use (or use preconfigured)",
    "use_sudo": "Use sudo for install command",
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
})
def install(ctx, project="all", build_config=None, generator=None,
            prefix=None, use_sudo=False):
    """Install the build artifacts of cmake project(s)."""
    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.install(prefix=prefix, use_sudo=use_sudo)


@task(help={
    "format":       "cpack.generator to use: TGZ, ZIP, ... (CPACK_GENERATOR)",
    "project":      TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator":    TASK_HELP4PARAM_GENERATOR,
    "package-dir":  "Override: CPACK_PACKAGE_DIRECTORY (optional)",
    "config":       "CPack config-file to use (default: CPackConfig.cmake)",
    "source":       "Create a source package (instead of: binary package)",
    "vendor":       "Override: CPACK_PACKAGE_VENDOR (optional)",
    "verbose":      "Run cpack in verbose mode (optional)",
    # -- OPTIONAL: Check if needed.
    "target": "CMake build target before cpack is used (optional)",
})
def pack(ctx, format=None, project="all", build_config=None, generator=None,
         target=None, package_dir=None, config=None,
         source=False, vendor=None, verbose=False):
    """Pack a source-code archive or a binary bundle/archive for cmake project(s)."""
    # MAYBE: cpack_defines
    if not format:
        format = CPACK_GENERATOR

    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        if target:
            cmake_project.build(target=target)
        cmake_project.pack(format=format, package_dir=package_dir,
                           config=config, source_bundle=source,
                           vendor=vendor, verbose=verbose)
        print()


@task(aliases=["update"], iterable=["define"], help={
    "define": TASK_HELP4PARAM_DEFINE,
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
})
def update_config(ctx, define, project="all", build_config=None, generator=None):
    """Update CMake build_dir configuration for cmake project(s)."""
    cmake_define_parts = define   # List of cmake definitions: NAME=VALUE
    cmake_defines_data = OrderedDict()
    bad_defines = []
    for name_value in cmake_define_parts:
        if "=" not in name_value or name_value.endswith("="):
            print("INVALID-DEFINE: %s (use schema: name=value)" % name_value)
            bad_defines.append(name_value)
            continue

        parts = name_value.split("=", 1)
        name, value = parts
        cmake_defines_data[name] = value

    if bad_defines:
        raise Exit("BAD-DEFINES: %s" % ", ".join(bad_defines))

    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.update(**cmake_defines_data)


@task(iterable=["arg"], help={
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "arg": "CMake build clean argument (optional, many)"
})
def clean(ctx, arg=None, project="all", build_config=None,
          dry_run=False, strict=True):
    """Clean cmake project(s) by using the build system."""
    cmake_args = arg or []
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         strict=True)   # MAYBE: strict=strict
    for cmake_project in cmake_projects:
        cmake_project.clean(args=cmake_args)     # MAYBE: dry_run=dry_run)


@task
def clean_and_ignore_failures(ctx, project="all", build_config=None, args=None,
                              dry_run=False):
    """Perform build-system clean target and ignore any failures (best-effort)."""
    clean(ctx, project=project, build_config=build_config, strict=False)


@task(iterable=["arg"], help={
    "arg": TASK_HELP4PARAM_INIT_ARG,
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
})
def reinit(ctx, project="all", build_config=None, generator=None, arg=None):
    """Reinit cmake projects (performs: cleanup, init)."""
    # -- HINT: Preserve pre-existing cmake_project.cmake_generator
    cmake_init_args = arg or None
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         init_args=cmake_init_args)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.reinit(args=cmake_init_args)    # PREPARED, TODO: dry_run=dry_run)


@task(iterable=["arg", "init_arg"], help={
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
    "arg": TASK_HELP4PARAM_ARG,
    "init-arg": TASK_HELP4PARAM_INIT_ARG,
})
def rebuild(ctx, project="all", build_config=None, generator=None,
            arg=None, init_arg=None):
    """Rebuild cmake projects (performs: clean, build)."""
    cmake_build_args = arg or []
    cmake_init_args = init_arg or [ ]
    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.rebuild(args=cmake_build_args, init_args=cmake_init_args)
    # PREPARED, TODO: dry_run=dry_run)


@task(iterable=["arg", "init_arg", "test-arg"], help={
    "project": TASK_HELP4PARAM_PROJECT,
    "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
    "generator": TASK_HELP4PARAM_GENERATOR,
    "arg": TASK_HELP4PARAM_ARG,
    "init-arg": TASK_HELP4PARAM_INIT_ARG,
    "test-arg": "CMake test arg (optional, many)",
    "use-test": "Perform CMake test step (optional)",
})
def redo(ctx, project="all", build_config=None, generator=None,
         arg=None, init_arg=None, test_arg=None, use_test=False):
    """Build cycle for cmake project(s) (performs: reinit, build, ...).

    Steps:

    - cmake.reinit
    - cmake.build
    - OPTIONAL: cmake.test (= ctest)  -- enabled via: --use-test option
    """
    cmake_build_args = arg or []
    cmake_init_args = init_arg or []
    ctest_args = test_arg or []
    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator,
                                         init_args=cmake_init_args)
    for cmake_project in cmake_projects:
        cmake_project.reinit(args=cmake_init_args)
        cmake_project.build(args=cmake_build_args)
        if use_test:
            cmake_project.test(args=ctest_args)


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
namespace.add_task(install)
namespace.add_task(pack)
namespace.add_task(update_config)


TASKS_CONFIG_DEFAULTS = {
    "cmake_generator": None,
    "cmake_toolchain": None,
    "cmake_install_prefix": None,
    "cmake_defines": None,
    "build_dir_schema": "build.{BUILD_CONFIG}",
    "build_config": BUILD_CONFIG_DEFAULT,
    "build_configs": [],
    "build_config_aliases": {}, # HINT: Map string -> sequence<string> (or string or callable)
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
