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

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
import sys
import os.path
from invoke import task, Collection
from invoke.util import cd
from path import Path
from codecs import open
import json

# -- TASK-LIBRARY:
from .cleanup import cleanup_tasks, cleanup_dirs


# -----------------------------------------------------------------------------
# TASK UTILITIES:
# -----------------------------------------------------------------------------
def _cmake_build(ctx, target=None, project="all", build_config=None,
                 generator=None, args=None, init_args=None, dry_run=False):
    extra = ""
    if build_config:
        extra = "--build_config={0}".format(build_config)
    if generator:
        extra += " --generator={0}".format(generator)
    if args:
        extra += " {0}".format(args)
    if init_args:
        extra += ' --init="{0}"'.format(init_args)

    # XXX dry_run
    target = target or "build"
    ctx.run('cmake-build --target={target} --project={project} {extra}'.format(
            target=target, project=project, extra=extra.strip()))


# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
@task
def init(ctx, project="all", build_config=None, generator=None, args=None):
    """Initialize all cmake projects."""
    _cmake_build(ctx, "init", project=project, build_config=build_config,
                 generator=generator, args=args)
    # XXX-OLD
    if False:
        cmake_projects = _cmake_select_projects(ctx, project)
        for cmake_project in cmake_projects:
            _cmake_project_load_generator_and_ensure_init(ctx, cmake_project,
                                                          generator, init_args=args)
        # cmake_generator = _cmake_project_load_generator(cmake_project)
        # if generator and (cmake_generator != generator):
        #     cmake_generator = generator
        # _cmake_ensure_init(ctx, cmake_project,
        #                    generator=cmake_generator, args=args)


@task
def build(ctx, project="all", build_config=None, args=None, generator=None, init_args=None):
    """Build one or all cmake projects."""
    _cmake_build(ctx, "build", project=project, build_config=build_config,
                 generator=generator, args=args, init_args=init_args)

    if False:
        cmake_projects = _cmake_select_projects(ctx, project)
        for cmake_project in cmake_projects:
            # cmake_generator = _cmake_project_load_generator(cmake_project)
            # if generator and (cmake_generator != generator):
            #     cmake_generator = generator
            # _cmake_ensure_init(ctx, cmake_project, generator=cmake_generator, args=init_args)
            _cmake_project_load_generator_and_ensure_init(ctx, cmake_project,
                                                          generator,
                                                          init_args=init_args)
            _cmake_build(ctx, cmake_project, args=args)


@task
def test(ctx, project="all", build_config=None, args=None, generator=None, init_args=None):
    """Test one or all cmake projects."""
    _cmake_build(ctx, "test", project=project, build_config=build_config,
                 generator=generator, args=args, init_args=init_args)
    if False:
        cmake_projects = _cmake_select_projects(ctx, project)
        for cmake_project in cmake_projects:
            _cmake_project_load_generator_and_ensure_init(ctx, cmake_project,
                                                          generator,
                                                          init_args=init_args)
            _cmake_test(ctx, cmake_project, args=args)


# @task
# def build_clean(ctx, project="all", args=None, generator=None, init_args=None):
#     """Build one or all cmake projects."""
#     more_build_args = args or ""
#     cmake_projects = _cmake_select_projects(ctx, project)
#     for cmake_project in cmake_projects:
#         _cmake_ensure_init(ctx, cmake_project,
#                            generator=generator, args=init_args)
#         _cmake_build(ctx, cmake_project, args="clean " + more_build_args)

@task
def clean(ctx, project="all", dry_run=False):
    """Cleanup all cmake projects."""
    cmake_projects = _cmake_select_projects(ctx, project)
    for cmake_project in cmake_projects:
        _cmake_cleanup(ctx, cmake_project, dry_run=dry_run)

    # BAD, AVOID: cleanup_dirs("**/build/", dry_run=dry_run)


@task
def reinit(ctx, project="all", generator=None, args=None, dry_run=False):
    """Reinit cmake projects."""
    clean(ctx, project=project, dry_run=dry_run)
    init(ctx, project=project, generator=generator, args=args)


@task
def rebuild(ctx, project="all", args=None, generator=None, init_args=None):
    """Rebuild one or all cmake projects."""
    build(ctx, project=project, args="clean", generator=generator, init_args=init_args)
    build(ctx, project=project, args=args, generator=generator, init_args=init_args)


@task
def all(ctx, project="all", args=None, generator=None, init_args=None, test_args=None):
    """Performs multiple stsps for one (or more) projects:

    - cmake.init
    - cmake.build
    - cmake.test (= ctest)
    """
    # init(ctx, project=project, generator=generator, args=init_args)
    build(ctx, project=project, args=args, generator=generator, init_args=init_args)
    test(ctx, project=project, args=test_args, generator=generator, init_args=init_args)


@task
def redo_all(ctx, project="all", args=None, generator=None, init_args=None, test_args=None):
    """Performs multiple steps for one (or more) projects:

    - cmake.reinit
    - cmake.build
    - cmake.test (= ctest)
    """
    reinit(ctx, project=project, generator=generator, args=init_args)
    build(ctx, project=project, args=args, generator=generator, init_args=init_args)
    test(ctx, project=project, args=test_args, generator=generator, init_args=init_args)


# -----------------------------------------------------------------------------
# TASK CONFIGURATION:
# -----------------------------------------------------------------------------
namespace = Collection()
namespace.add_task(all)
namespace.add_task(redo_all)
namespace.add_task(init)
namespace.add_task(build, default=True)
namespace.add_task(test)
namespace.add_task(clean)
namespace.add_task(reinit)
namespace.add_task(rebuild)
namespace.configure({
    "cmake": {
        "build_dir_schema": "build.{OS}_{CPU_ARCH}_{BUILD_CONFIG}",
        "project_dirs": [
            CMAKE_PROJECT_DIRS
        ],
        "generator": None,
        "toolchain": None,
    },
})

# -- REGISTER CLEANUP TASKS:
cleanup_tasks.add_task(clean, "clean_cmake")
cleanup_tasks.configure(namespace.configuration())
