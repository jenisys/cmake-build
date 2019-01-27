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
from ._tasklet_cleanup import cleanup_tasks, cleanup_dirs


# -----------------------------------------------------------------------------
# CMAKE PROJECT CONFIGURATION:
# -----------------------------------------------------------------------------
BUILD_DIR = "build"
BUILD_DIR_SCHEMA = "build.{BUILD_CONFIG}"
BUILD_CONFIG_DEFAULT = "Default"
CMAKE_PROJECT_DIRS = [
    # "01_Program_example1",
    # "01_Program_example2",
    # "CTEST_example1",
]

CMAKE_GENERATOR_ALIAS_MAP = {
    "ninja": "Ninja",
    "make": "Unix Makefiles",
}

CMAKE_DEFAULT_GENERATOR = "make"    # EMPTY means Makefiles ('Unix Makefiles')


# -----------------------------------------------------------------------------
# CMAKE UTILITY CLASSES:
# -----------------------------------------------------------------------------
class Unknown(object): pass

class PersistentData(object):
    FILE_BASENAME = "persistent.json"

    def __init__(self, data_dir, **kwargs):
        self.data_dir = Path(data_dir)
        self.data = kwargs
    
    @property
    def filename(self):
        return self.data_dir/self.FILE_BASENAME

    def make_data(self):
        return self.data

    def get(self, name, default=None):
        value = getattr(self, name, Unknown)
        if value is Unknown:
            value = self.data.get(name, default)
        return value

    def exists(self):
        filename = self.filename
        assert not filename.exists() or filename.isfile()
        return filename.exists()

    def clear(self):
        # -- KEEP: self.data_dir
        self.data = {}

    def assign(self, data):
        # -- WORKS WITH: this-class or dict-like
        the_data = data
        if isinstance(data, self.__class__):
            the_data = data.data
        self.data = the_data.copy()
        
    @classmethod
    def parse(cls, text, encoding=None, project_dir=None):
        encoding = encoding or "UTF-8"
        data = json.loads(text, encoding=encoding)
        return data

    def dump(self, readable=True):
        """Dumps data as text."""
        data = self.make_data()
        extra_args = {}
        if readable:
            extra_args = dict(sort_keys=True, indent=4)
        return json.dumps(data, **extra_args)

    def load(self):
        filename = self.filename
        if not filename.exists():
            self.data = {}
            return self
        
        with open(filename, "t", encoding="UTF-8") as f:
            text = f.read()
            data = self.parse(text)
            self.clear()
            self.assign(data)
        return self
    
    def save(self):
        filename = self.filename
        dirname = filename.dirname()
        dirname.makedirs_p()
        with open(filename, "wb") as f:
            text_data = self.dump()
            f.write(text_data)
        return self

class CMakeProjectPersistentData(PersistentData):
    FILE_BASENAME = ".cmake_build.json"

    def __init__(self, project_dir, build_dir, generator=None, toolchain=None, **kwargs):
        project_dir = Path(project_dir or "")
        data_dir = project_dir/build_dir
        kwargs["generator"] = generator
        kwargs["toolchain"] = toolchain
        super(CMakeProjectPersistentData, self).__init__(data_dir, **kwargs)
        self.project_dir = project_dir
    
    @property
    def generator(self):
        return self.get("generator", None)

    @property
    def toolchain(self):
        return self.get("toolchain", None)


class CMakeProjectPersistentData0(object):
    FILE_BASENAME = ".cmake_build.json"

    def __init__(self, project_dir, generator=None, toolchain=None, **kwargs):
        self.project_dir = Path(project_dir)
        self.generator = generator
        self.toolchain = toolchain
        self.data = kwargs
    
    @property
    def filename(self):
        return self.project_dir/self.FILE_BASENAME

    def make_data(self):
        self.data["generator"] = self.generator
        self.data["toolchain"] = self.toolchain
        return self.data

    def get(self, name, default=None):
        value = getattr(self, name, Unknown)
        if value is Unknown:
            value = self.data.get(name, default)
        return value

    def exists(self):
        filename = self.filename
        assert not filename.exists() or filename.isfile()
        return filename.exists()

    def clear(self):
        # -- KEEP: self.project_dir
        self.generator = None
        self.toolchain = None
        self.data = {}

    def assign(self, data):
        # -- WORKS WITH: this-class or dict-like
        self.generator = data.get("generator", None)
        self.toolchain = data.get("toolchain", None)
        the_data = data
        if isinstance(data, self.__class__):
            the_data = data.data
        self.data = the_data.copy()
        
    @classmethod
    def parse(cls, text, encoding=None, project_dir=None):
        encoding = encoding or "UTF-8"
        data = json.loads(text, encoding=encoding)
        return data
        # generator = data.get("generator", None)
        # toolchain = data.get("toolchain", None)
        # return cls(project_dir=project_dir, generator=generator,
        #         toolchain=toolchain, **data)

    def dump(self):
        data = self.make_data()
        return json.dumps(data, sort_keys=True, indent=4)

    def load(self):
        filename = self.filename
        if not filename.exists():
            self.data = {}
            return self
        
        with open(filename, "t", encoding="UTF-8") as f:
            text = f.read()
            data = self.parse(text)
            self.clear()
            self.assign(data)
        return self
    
    def save(self):
        filename = self.filename
        dirname = filename.dirname()
        dirname.makedirs_p()
        with open(filename, "wb") as f:
            text_data = self.dump()
            f.write(text_data)
        return self

# @wip
class CMakeProject(object):
    def __init__(self, project_dir=None, project_build_dir=None, 
                 cmake_generator=None, build_dir=BUILD_DIR, ctx=None):
        build_dir = build_dir or BUILD_DIR
        project_dir = Path(project_dir)
        if project_dir and not project_build_dir:
            project_build_dir = project_dir/build_dir
        if not project_dir and project_build_dir:
            project_build_dir = Path(project_build_dir)
            project_dir = project_build_dir.dirname()
            build_dir = project_build_dir.basename()

        self.project_dir = project_dir
        self.project_build_dir = project_build_dir
        self.cmake_generator = cmake_generator
        self.cmake_stored_generator = self.load_cmake_generator()
        self.build_dir = build_dir
        self.ctx = ctx

    @property
    def initialized(self):
        return (self.project_build_dir.exists() and self.cmake_stored_generator
                and self.cmake_stored_generator == self.cmake_generator)

    def cleanup(self):
        if self.project_build_dir.isdir():
            self.project_build_dir.rmtree_p()
    
    def init(self, cmake_generator):
        if self.initialized:
            # -- CASE: ALREADY DONE w/ same cmake_generator.
            return
        if self.project_build_dir.isdir():
            self.cleanup()
        self.project_build_dir.makedirs_p()
        # XXX-TODO self.ctx.run("cmake")        
        self.store_cmake_generator(cmake_generator)

    def store_cmake_generator(self, cmake_generator):
        marker_file = self.project_build_dir/".cmake_generator"
        marker_file.write_text(cmake_generator)

    def load_cmake_generator(self, cmake_generator_default=None):
        marker_file = self.project_build_dir/".cmake_generator"
        if marker_file.exists():
            return marker_file.open().read().strip()
        return cmake_generator_default

    @classmethod
    def from_project_dir(cls, ctx, project_dir, cmake_generator=None, build_dir=BUILD_DIR):
        project_dir = Path(project_dir)
        project_build_dir = project_dir/build_dir
        return cls(project_dir, project_build_dir, 
                   cmake_generator=cmake_generator, build_dir=build_dir, ctx=ctx)

    @classmethod
    def from_project_build_dir(cls, ctx, project_build_dir, cmake_generator=None):
        project_build_dir = Path(project_build_dir)
        project_dir = project_build_dir.dirname()
        build_dir = project_build_dir.basename()
        return cls(project_dir, project_build_dir,
                   cmake_generator=cmake_generator, build_dir=build_dir, ctx=ctx)


# @wip
class __DISABLED_CMakeProject_0(object):
    def __init__(self, project_dir=None, project_build_dir=None, 
                 cmake_generator=None, build_dir=BUILD_DIR, ctx=None):
        build_dir = build_dir or BUILD_DIR
        project_dir = Path(project_dir)
        if project_dir and not project_build_dir:
            project_build_dir = project_dir/build_dir
        if not project_dir and project_build_dir:
            project_build_dir = Path(project_build_dir)
            project_dir = project_build_dir.dirname()
            build_dir = project_build_dir.basename()

        self.project_dir = project_dir
        self.project_build_dir = project_build_dir
        self.cmake_generator = cmake_generator
        self.cmake_stored_generator = self.load_cmake_generator()
        self.build_dir = build_dir
        self.ctx = ctx

    @property
    def initialized(self):
        return (self.project_build_dir.exists() and self.cmake_stored_generator
                and self.cmake_stored_generator == self.cmake_generator)

    def cleanup(self):
        if self.project_build_dir.isdir():
            self.project_build_dir.rmtree_p()
    
    def init(self, cmake_generator):
        if self.initialized:
            # -- CASE: ALREADY DONE w/ same cmake_generator.
            return
        if self.project_build_dir.isdir():
            self.cleanup()
        self.project_build_dir.makedirs_p()
        # XXX-TODO self.ctx.run("cmake")        
        self.store_cmake_generator(cmake_generator)

    def store_cmake_generator(self, cmake_generator):
        marker_file = self.project_build_dir/".cmake_generator"
        marker_file.write_text(cmake_generator)

    def load_cmake_generator(self, cmake_generator_default=None):
        marker_file = self.project_build_dir/".cmake_generator"
        if marker_file.exists():
            return marker_file.open().read().strip()
        return cmake_generator_default

    @classmethod
    def from_project_dir(cls, ctx, project_dir, cmake_generator=None, build_dir=BUILD_DIR):
        project_dir = Path(project_dir)
        project_build_dir = project_dir/build_dir
        return cls(project_dir, project_build_dir, 
                   cmake_generator=cmake_generator, build_dir=build_dir, ctx=ctx)

    @classmethod
    def from_project_build_dir(cls, ctx, project_build_dir, cmake_generator=None):
        project_build_dir = Path(project_build_dir)
        project_dir = project_build_dir.dirname()
        build_dir = project_build_dir.basename()
        return cls(project_dir, project_build_dir,
                   cmake_generator=cmake_generator, build_dir=build_dir, ctx=ctx)

# -----------------------------------------------------------------------------
# CMAKE UTILS:
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
    project_build_dir = project_dir/build_dir
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
    project_build_dir = project_dir/build_dir
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
    project_build_dir = project_dir/build_dir
    project_build_dir.makedirs_p()

    with cd(project_build_dir):
        print("CMAKE-TEST: %s" % project_build_dir)  # XXX os.getcwd())
        ctx.run("ctest %s" % build_args)

def _cmake_ensure_init(ctx, project_dir, generator=None, args=None, build_dir=BUILD_DIR):
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_dir = Path(project_dir)
    project_build_dir = project_dir/build_dir
    cmake_generator_marker_file = project_build_dir/".cmake_generator"
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
    project_build_dir = project_dir/build_dir
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
    project_build_dir = Path(cmake_project)/build_dir
    cmake_generator_marker_file = project_build_dir/".cmake_generator"
    if cmake_generator_marker_file.exists():
        current_cmake_generator = cmake_generator_marker_file.open().read().strip()
        return current_cmake_generator
    # -- OTHERWISE:
    return cmake_generator_default


def _cmake_project_store_generator(cmake_project, cmake_generator, build_config=None):
    build_dir = _cmake_make_build_dir(ctx, build_config)
    project_build_dir = Path(cmake_project)/BUILD_DIR
    cmake_generator_marker_file = project_build_dir/".cmake_generator"
    cmake_generator_marker_file.write_text(cmake_generator)


def _cmake_project_load_generator_and_ensure_init(ctx, cmake_project, generator=None, 
                                           init_args=None, build_config=None):
    cmake_generator = _cmake_project_load_generator(cmake_project)
    if generator and (cmake_generator != generator):
        cmake_generator = generator
    _cmake_ensure_init(ctx, cmake_project, generator=cmake_generator, args=init_args)
    return cmake_generator


# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
@task
def init(ctx, project="all", generator=None, args=None):
    """Initialize all cmake projects."""
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
def build(ctx, project="all", args=None, generator=None, init_args=None):
    """Build one or all cmake projects."""
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
def test(ctx, project="all", args=None, generator=None, init_args=None):
    """Test one or all cmake projects."""
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
