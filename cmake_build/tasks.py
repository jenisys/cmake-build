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
import six

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
from invoke import task, Collection
from path import Path

# -- TASK-LIBRARY:
from .tasklet.cleanup import cleanup_tasks
from .model import CMakeProject, CMakeProjectData, CMakeBuildRunner, BuildConfig


# -----------------------------------------------------------------------------
# TASK UTILITIES:
# -----------------------------------------------------------------------------
def require_build_config_is_valid(ctx, build_config):
    build_configs = ctx.config.build_configs or {}
    build_config_aliases = ctx.config.build_config_aliases or {}
    build_config_alias = build_config_aliases.get(build_config, None)
    if build_config_alias:
        build_config_data = build_configs.get(build_config_alias)

    build_config_data = build_configs.get(build_config)
    if build_config_data:
        return True

    # -- CASE: UNKNOWN BUILD-CONFIG
    if build_config_alias:
        expected = sorted(list(build_configs.keys()))
        expected.remove("all")
        message = "UNKOWN-ALIAS-VALUE: build_config=%s (alias=%s, epxected=%s)" % \
                  (build_config, build_config_alias, expected)
        print(message)
        # assert False, message
    else:
        expected = set(list(build_config_aliases.keys()))
        expected.update((list(build_configs.keys())))
        expected.remove("all")
        expected = sorted(expected)
        message = "UNKNOWN: build_config=%s (expected: %s)" % (build_config, expected)
        print(message)
        # assert False, message
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

    for project_dir in project_dirs:
        project_dir = Path(project_dir)
        if not project_dir.isdir():
            if verbose:
                print("CMAKE-BUILD: Skip project {0} (NOT-FOUND)".format(
                      project_dir))
            continue
        yield project_dir


def make_build_config(ctx, name=None):
    name = name or "debug"
    config = ctx.config
    build_config_defaults = CMakeProjectData().data
    build_config_defaults["cmake_generator"] = ctx.config.cmake_generator or "ninja"
    build_config_defaults["cmake_toolchain"] = ctx.config.cmake_toolchain
    build_config_defaults["cmake_build_type"] = None
    build_config_defaults["cmake_defines"] = ctx.config.cmake_defines or []
    build_config_defaults["build_dir_schema"] = ctx.config.build_dir_schema
    build_config_data = {}
    build_config_data.update(build_config_defaults)
    build_config_data2 = config.build_configs.get(name) or {}
    build_config_data.update(build_config_data2)
    return BuildConfig(name, build_config_data)


def make_cmake_project(ctx, project_dir, build_config=None, **kwargs):
    cmake_generator = kwargs.pop("generator", None)
    build_config_default = ctx.config.build_config_aliases.get("default", "debug")
    build_config = build_config or build_config_default
    require_build_config_is_valid(ctx, build_config)

    build_config = make_build_config(ctx, build_config)
    cmake_project = CMakeProject(ctx, project_dir, build_config=build_config,
                                 cmake_generator=cmake_generator)
    print("IGNORE-ARGS: %r" % kwargs)
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
                                         init_args=args, generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.init()


@task
def build(ctx, project="all", build_config=None, generator=None, args=None, init_args=None):
    """Build one or all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         args=args, init_args=init_args, generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.build()



@task
def test(ctx, project="all", build_config=None, generator=None, args=None, init_args=None):
    """Test one or all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         args=args, init_args=init_args, generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.test()


@task
def clean(ctx, project="all", build_config=None, dry_run=False):
    """Cleanup all cmake projects."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         verbose=False)
    for cmake_project in cmake_projects:
        cmake_project.clean()     # TODO: dry_run=dry_run)


@task
def reinit(ctx, project="all", build_config=None, generator=None, args=None, dry_run=False):
    """Reinit cmake projects (performs: cleanup, init)."""
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         init_args=args, verbose=False)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.reinit()    # PREPARED, TODO: dry_run=dry_run)


@task
def rebuild(ctx, project="all", build_config=None, generator=None, args=None, init_args=None):
    """Rebuild one or all CMake projects (performs: clean, build)."""
    # build(ctx, project=project, build_config=build_config, args="clean", generator=generator, init_args=init_args)
    # build(ctx, project=project, build_config=build_config, args=args, generator=generator, init_args=init_args)
    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         init_args=args, verbose=False)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.rebuild()    # PREPARED, TODO: dry_run=dry_run)


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
        cmake_project.build()
        cmake_project.test()

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
        cmake_project.reinit()
        cmake_project.build()
        cmake_project.test()


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
    config = ctx.config
    print("cmake_generator: %s" % ctx.config.cmake_generator)
    cmake_build_show_build_configs(config.build_configs)
    cmake_build_show_projects(config.projects)
    pprint(config, indent=4)
    print("-------------------------")
    pprint(dict(config), indent=4)
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
    "build_dir_schema": "build.{BUILD_CONFIG}",
    "build_configs": {},
    "build_config_aliases": {
        "default": "debug",
    },
    "projects": [],
}
namespace.configure(TASKS_CONFIG_DEFAULTS)


# -- REGISTER CLEANUP TASKS:
cleanup_tasks.add_task(clean, "clean_cmake-build")
cleanup_tasks.configure(namespace.configuration())
