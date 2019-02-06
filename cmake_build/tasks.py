# -*- coding: UTF-8 -*-
# pylint: disable=wrong-import-position, wrong-import-order
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

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
from invoke import task, Collection
from invoke.exceptions import Failure, Exit
from path import Path

# -- TASK-LIBRARY:
from .tasklet.cleanup import cleanup_tasks
from .model import CMakeProject, CMakeProjectData, CMakeBuildRunner, BuildConfig


# -----------------------------------------------------------------------------
# TASK UTILITIES:
# -----------------------------------------------------------------------------
# XXX-JE-WORKMARK-CHECK-IF-REALLY-NEEDED:
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
    build_configs_map = {}
    for build_config in build_configs:
        if isinstance(build_config, six.string_types):
            build_configs_map[build_config] = {}
        elif isinstance(build_config, dict):
            assert len(build_config) == 1, "ENSURE: length=1 (%r)" % build_config
            name = list(build_config.keys())[0]
            build_config_data = build_config[name]
            build_configs_map[name] = build_config_data
        else:
            raise ValueError("UNEXPECTED: %r (expected: string, dict(size=1)" % build_config)
    return build_configs_map


def require_build_config_is_valid(ctx, build_config):
    if not build_config:
        build_config = ctx.config.build_config or "debug"
    build_configs = ctx.config.build_configs or []
    build_configs_map = ctx.config.get("build_configs_map", None)
    if not build_configs_map:
        build_configs_map = make_build_configs_map(build_configs)
        ctx.config.build_configs_map = build_configs_map

    # DISABLED: build_config_aliases = ctx.config.build_config_aliases or {}
    # DISABLED: build_config_alias = build_config_aliases.get(build_config, None)
    # DISABLED: if build_config_alias:
    # DISABLED:     build_config_data = build_configs.get(build_config_alias)
    # DISABLED: else:
    build_config_data = build_configs_map.get(build_config)

    if build_config_data is not None:
        return True

    # DISABLED:
    #  -- CASE: UNKNOWN BUILD-CONFIG
    # if build_config_alias:
    #     expected = sorted(list(build_configs.keys()))
    #     if "all" in expected:
    #         expected.remove("all")
    #     expected = ", ".join(sorted(expected))
    #     message = "UNKOWN-BUILD-CONFIG: %s (alias=%s, expected=%s)" % \
    #               (build_config_alias, build_config, expected)
    #     # print(message)
    # else:
    # DISABLED: expected = set(list(build_config_aliases.keys()))
    # DISABLED: expected.update((list(build_configs.keys())))
    # DISABLED: if "all" in expected:
    # DISABLED:     expected.remove("all")
    expected = ", ".join(sorted(list(build_configs_map.keys())))
    message = "UNKNOWN-BUILD-CONFIG: %s (expected: %s)" % (build_config, expected)
    print(message)
    print(repr(ctx.config.build_configs_map))
    # DISABLED: print(repr(ctx.config.build_config_aliases))
    raise Exit(message)
    return False


def cmake_select_project_dirs(ctx, projects=None, verbose=False):
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
        raise Exit(message)


def make_build_config(ctx, name=None):
    name = name or ctx.config.build_config or "default"
    # DISABLED: aliased = ctx.config.build_config_aliases.get(name)
    # DISABLED: if aliased:
    # DISABLED:     name = aliased
    # DISABLED:     if not isinstance(name, six.string_types):
    # DISABLED:         name = name[0]

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


def make_cmake_project(ctx, project_dir, build_config=None, **kwargs):
    if not ctx.config.build_configs_map:
        # -- LAZY-INIT: Build build_configs_map once from build_configs list.
        build_configs_map = make_build_configs_map(ctx.config.build_configs)
        ctx.config.build_configs_map = build_configs_map
        # MAYBE-MORE:
        # CMakeBuildConfigNormalizer.normalize(ctx.config)

    cmake_generator = kwargs.pop("generator", None)
    # DISABLED: build_config_default = ctx.config.build_config_aliases.get("default", "debug")
    build_config_default = ctx.config.build_config or "debug"
    build_config = build_config or build_config_default
    require_build_config_is_valid(ctx, build_config)
    # DISABLED: build_config_aliased = ctx.config.build_config_aliases.get(build_config)
    # DISABLED: if build_config_aliased:
    # DISABLED:     build_config = build_config_aliased

    build_config = make_build_config(ctx, build_config)
    cmake_project = CMakeProject(ctx, project_dir, build_config=build_config,
                                 cmake_generator=cmake_generator)
    if kwargs:
        print("cmake_project: IGNORED_ARGS=%r" % kwargs)
    return cmake_project


def make_cmake_projects(ctx, projects, build_config=None, verbose=True, **kwargs):
    project_dirs = cmake_select_project_dirs(ctx, projects, verbose=verbose)
    cmake_projects = []
    for project_dir in project_dirs:
        cmake_project = make_cmake_project(ctx, project_dir, build_config, **kwargs)
        cmake_projects.append(cmake_project)
    return cmake_projects


# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
@task
def init(ctx, project="all", build_config=None, generator=None, args=None):
    """Initialize all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
                                         # DISABLED: init_args=args, generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.init(args=args)


@task
def build(ctx, project="all", build_config=None, generator=None, args=None, init_args=None):
    """Build one or all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.build(args=args, init_args=init_args)



@task
def test(ctx, project="all", build_config=None, generator=None, args=None, init_args=None):
    """Test one or all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.test(args=args, init_args=init_args)


@task
def clean(ctx, project="all", build_config=None, args=None, dry_run=False):
    """Cleanup all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         verbose=False)
    for cmake_project in cmake_projects:
        cmake_project.clean(args=args)     # TODO: dry_run=dry_run)


@task
def reinit(ctx, project="all", build_config=None, generator=None, args=None, dry_run=False):
    """Reinit cmake projects (performs: cleanup, init)."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         init_args=args, verbose=False)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.reinit(args=args)    # PREPARED, TODO: dry_run=dry_run)


@task
def rebuild(ctx, project="all", build_config=None, generator=None, args=None, init_args=None):
    """Rebuild one or all CMake projects (performs: clean, build)."""
    # build(ctx, project=project, build_config=build_config, args="clean", generator=generator, init_args=init_args)
    # build(ctx, project=project, build_config=build_config, args=args, generator=generator, init_args=init_args)
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         verbose=False)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.rebuild(args=args, init_args=init_args)    # PREPARED, TODO: dry_run=dry_run)


@task
def all(ctx, project="all", generator=None, build_config=None, args=None, init_args=None, test_args=None):
    """Performs multiple stsps for one (or more) projects:

    - cmake.init
    - cmake.build
    - cmake.test (= ctest)
    """
    # build(ctx, project=project, build_config=build_config, args=args, generator=generator, init_args=init_args)
    # test(ctx, project=project, build_config=build_config, args=test_args)

    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         init_args=args, verbose=False)
    for cmake_project in cmake_projects:
        cmake_project.build(args=args, init_args=init_args)
        cmake_project.test(args=test_args)

@task
def redo(ctx, project="all", build_config=None, generator=None, args=None, init_args=None, test_args=None):
    """Performs multiple steps for one (or more) projects:

    - cmake.reinit
    - cmake.build
    - cmake.test (= ctest)
    """
    # reinit(ctx, project=project, build_config=build_config, generator=generator, args=init_args)
    # build(ctx, project=project, build_config=build_config, args=args)
    # test(ctx, project=project, build_config=build_config, args=test_args)
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator, init_args=args)
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
    cmake_build_show_build_configs(config.build_configs)
    cmake_build_show_projects(ctx.config.projects)
    pprint(ctx.config, indent=4)
    print("-------------------------")
    pprint(dict(ctx.config), indent=4)
    # return 1/0


# -----------------------------------------------------------------------------
# TASK CONFIGURATION:
# -----------------------------------------------------------------------------
namespace = Collection(all, redo, init, test, clean, reinit, rebuild, config)
namespace.add_task(build, default=True)
# namespace.add_task(all)
# namespace.add_task(redo)
# namespace.add_task(init)
# namespace.add_task(test)
# namespace.add_task(clean)
# namespace.add_task(reinit)
# namespace.add_task(rebuild)
# namespace.add_task(config)

TASKS_CONFIG_DEFAULTS = {
    "cmake_generator": None,
    "cmake_toolchain": None,
    # "cmake_defines": [],
    "build_dir_schema": "build.{BUILD_CONFIG}",
    "build_config": "debug",
    "build_configs": [],
    "build_configs_map": {},
    "projects": [],
    # DISABLED: "build_config_aliases": {
    # DISABLED:     "default": "debug",
    # DISABLED: },
}
namespace.configure(TASKS_CONFIG_DEFAULTS)


# -- REGISTER CLEANUP TASKS:
cleanup_tasks.add_task(clean, "clean_cmake-build")
cleanup_tasks.configure(namespace.configuration())
