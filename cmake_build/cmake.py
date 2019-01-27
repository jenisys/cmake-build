# -*- coding: UTF-8 -*-
"""
This module contains utility functions to simplify usage of `CMake`_.

.. _CMake: https://cmake.org/
"""

from __future__ import absolute_import, print_function
from .model import CMakeProject, CMakeProjectPersistentData
from invoke.util import cd


# -----------------------------------------------------------------------------
# CMAKE PROJECT CONFIGURATION CONSTANTS:
# -----------------------------------------------------------------------------
BUILD_DIR = "build"
BUILD_DIR_SCHEMA = "build.{BUILD_CONFIG}"
BUILD_CONFIG_DEFAULT = "Default"

CMAKE_DEFAULT_GENERATOR = "make"    # EMPTY means Makefiles ('Unix Makefiles')
CMAKE_GENERATOR_ALIAS_MAP = {
    "ninja": "Ninja",
    "make": "Unix Makefiles",
}


# -----------------------------------------------------------------------------
# OLD CMAKE UTILS:
# -----------------------------------------------------------------------------
def _cmake_make_build_dir(ctx, build_config, **kwargs):
    build_dir_schema = ctx.cmake.build_dir_schema or BUILD_DIR_SCHEMA
    build_dir = build_dir_schema.format(BUILD_CONFIG=build_config)
    return Path(build_dir)


def _cmake_init(ctx, project_dir, build_config=None, generator=None, args=None, build_dir=BUILD_DIR):
    if args is None:
        args = ""
    if not build_config:
        build_config = ctx.cmake.build_config_default or BUILD_CONFIG_DEFAULT
    cmake_generator = _cmake_use_generator(ctx, generator)
    if cmake_generator:
        cmake_generator_name = (CMAKE_GENERATOR_ALIAS_MAP.get(cmake_generator)
                                or cmake_generator)
        cmake_generator_arg = "-G '%s' " % cmake_generator_name
        args = cmake_generator_arg + args

    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_dir = Path(project_dir)
    project_build_dir = project_dir / build_dir
    project_build_dir.makedirs_p()

    with ctx.cd(project_build_dir):
        print("CMAKE-INIT: %s (using cmake.generator=%s)" % \
              (project_build_dir, cmake_generator))
        ctx.run("cmake %s .." % args)
        # -- FINALLY: If cmake-init worked, store used cmake_generator.
        cmake_generator_marker_file = Path(".cmake_generator")
        cmake_generator_marker_file.write_text(cmake_generator)


def _cmake_build(ctx, project_dir, args=None, generator=None, build_dir=BUILD_DIR):
    build_args = ""
    if args:
        build_args = "-- %s" % args
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_dir = Path(project_dir)
    project_build_dir = project_dir / build_dir
    project_build_dir.makedirs_p()

    with cd(project_build_dir):
        print("CMAKE-BUILD: %s" % project_build_dir)  # XXX os.getcwd())
        ctx.run("cmake --build . %s" % build_args)


def _cmake_test(ctx, project_dir, args=None, generator=None, build_dir=BUILD_DIR):
    build_args = ""
    if args:
        build_args = " ".join(args)
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_dir = Path(project_dir)
    project_build_dir = project_dir / build_dir
    project_build_dir.makedirs_p()

    with cd(project_build_dir):
        print("CMAKE-TEST: %s" % project_build_dir)  # XXX os.getcwd())
        ctx.run("ctest %s" % build_args)


def _cmake_ensure_init(ctx, project_dir, generator=None, args=None, build_dir=BUILD_DIR):
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_dir = Path(project_dir)
    project_build_dir = project_dir / build_dir
    cmake_generator_marker_file = project_build_dir / ".cmake_generator"
    if cmake_generator_marker_file.exists():
        cmake_generator1 = cmake_generator_marker_file.open().read().strip()
        cmake_generator2 = _cmake_use_generator(ctx, generator)
        if cmake_generator1 == cmake_generator2:
            print("CMAKE-INIT:  %s directory exists already (SKIPPED, generator=%s)." % \
                  (project_build_dir, cmake_generator1))
            return
        else:
            print("CMAKE-REINIT %s: Use generator=%s (was: %s)" % \
                  (project_build_dir, cmake_generator2, cmake_generator1))
            _cmake_cleanup(ctx, project_dir)

    # -- OTHERWISE:
    _cmake_init(ctx, project_dir, generator=generator, args=args, build_dir=build_dir)


def _cmake_cleanup(ctx, project_dir, build_dir=BUILD_DIR, dry_run=False):
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_dir = Path(project_dir)
    project_build_dir = project_dir / build_dir
    if dry_run:
        print("REMOVE_DIR: %s (DRY-RUN SIMULATED)" % project_build_dir)
    elif project_build_dir.isdir():
        print("RMTREE: %s" % project_build_dir)
        project_build_dir.rmtree_p()


def _cmake_select_projects(ctx, project):
    cmake_projects = ctx.cmake.project_dirs or CMAKE_PROJECT_DIRS
    if project and project != "all":
        cmake_projects = [project]
    return cmake_projects


def _cmake_use_generator(ctx, cmake_generator=None):
    default_cmake_generator = ctx.cmake.generator or CMAKE_DEFAULT_GENERATOR
    if cmake_generator is None:
        cmake_generator = default_cmake_generator
    return cmake_generator


def _cmake_project_load_generator(cmake_project, cmake_generator_default=None, build_config=None):
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_build_dir = Path(cmake_project) / build_dir
    cmake_generator_marker_file = project_build_dir / ".cmake_generator"
    if cmake_generator_marker_file.exists():
        current_cmake_generator = cmake_generator_marker_file.open().read().strip()
        return current_cmake_generator
    # -- OTHERWISE:
    return cmake_generator_default


def _cmake_project_store_generator(cmake_project, cmake_generator, build_config=None):
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_build_dir = Path(cmake_project) / BUILD_DIR
    cmake_generator_marker_file = project_build_dir / ".cmake_generator"
    cmake_generator_marker_file.write_text(cmake_generator)


def _cmake_project_load_generator_and_ensure_init(ctx, cmake_project, generator=None,
                                                  init_args=None, build_config=None):
    cmake_generator = _cmake_project_load_generator(cmake_project)
    if generator and (cmake_generator != generator):
        cmake_generator = generator
    _cmake_ensure_init(ctx, cmake_project, generator=cmake_generator, args=init_args)
    return cmake_generator

# -----------------------------------------------------------------------------
# CMAKE UTILITY CLASSES:
# -----------------------------------------------------------------------------
class Context(object):
    def __init__(self, config=None):
        self.config = config


# -----------------------------------------------------------------------------
# CMAKE UTILS:
# -----------------------------------------------------------------------------
def make_project_build_dir(ctx, build_config=None):
    config = ctx.config
    build_config = build_config or config.defaults.build_config or BUILD_CONFIG_DEFAULT
    build_dir_schema = config.build_dir_schema or BUILD_DIR_SCHEMA
    return build_dir_schema.format(BUILD_CONFIG=build_config)


def make_cmake_project(ctx, project_dir, build_config=None, generator=None):
    project_build_dir = make_project_build_dir(ctx, build_config)
    return CMakeProject(ctx, project_dir, project_build_dir)


def cmake_init(ctx, project_dir, build_config=None, generator=None, args=None):
    cmake_project = make_cmake_project(ctx, project_dir,
                                       build_config=build_config, generator=generator)
    cmake_project.init(args)
    if False:
        if args is None:
            args = ""
        if not build_config:
            build_config = ctx.cmake.build_config_default or BUILD_CONFIG_DEFAULT
        cmake_generator = _cmake_use_generator(ctx, generator)
        if cmake_generator:
            cmake_generator_name = (CMAKE_GENERATOR_ALIAS_MAP.get(cmake_generator)
                                    or cmake_generator)
            cmake_generator_arg = "-G '%s' " % cmake_generator_name
            args = cmake_generator_arg + args

        build_dir = _cmake_make_build_dir(ctx, build_config)
        project_dir = Path(project_dir)
        project_build_dir = project_dir / build_dir
        project_build_dir.makedirs_p()

        with ctx.cd(project_build_dir):
            print("CMAKE-INIT: %s (using cmake.generator=%s)" % \
                  (project_build_dir, cmake_generator))
            ctx.run("cmake %s .." % args)
            # -- FINALLY: If cmake-init worked, store used cmake_generator.
            cmake_generator_marker_file = Path(".cmake_generator")
            cmake_generator_marker_file.write_text(cmake_generator)


def cmake_build(ctx, project_dir, build_config=None, args=None, init_args=None, generator=None):
    cmake_project = make_cmake_project(ctx, project_dir,
                                       build_config=build_config, generator=generator)
    cmake_project.ensure_init(init_args)
    cmake_project.build(args)

    if False:
        build_args = ""
        if args:
            build_args = "-- %s" % args
        build_dir = _cmake_make_build_dir(ctx, build_config)
        project_dir = Path(project_dir)
        project_build_dir = project_dir / build_dir
        project_build_dir.makedirs_p()

        with cd(project_build_dir):
            print("CMAKE-BUILD: %s" % project_build_dir)  # XXX os.getcwd())
            ctx.run("cmake --build . %s" % build_args)


def cmake_test(ctx, project_dir, build_config=None, args=None, init_args=None, generator=None):
    cmake_project = make_cmake_project(ctx, project_dir,
                                       build_config=build_config, generator=generator)
    cmake_project.ensure_init(init_args)
    cmake_project.ctest(args)

    if False:
        build_args = ""
        if args:
            build_args = " ".join(args)
        build_dir = _cmake_make_build_dir(ctx, build_config)
        project_dir = Path(project_dir)
        project_build_dir = project_dir / build_dir
        project_build_dir.makedirs_p()

        with cd(project_build_dir):
            print("CMAKE-TEST: %s" % project_build_dir)  # XXX os.getcwd())
            ctx.run("ctest %s" % build_args)

def cmake_cleanup(ctx, project_dir, build_config=BUILD_DIR, dry_run=False):
    cmake_project = make_cmake_project(ctx, project_dir, build_config=build_config)
    cmake_project.cleanup()

    if False:
        build_dir = _cmake_make_build_dir(ctx, build_config)
        project_dir = Path(project_dir)
        project_build_dir = project_dir / build_dir
        if dry_run:
            print("REMOVE_DIR: %s (DRY-RUN SIMULATED)" % project_build_dir)
        elif project_build_dir.isdir():
            print("RMTREE: %s" % project_build_dir)
            project_build_dir.rmtree_p()
