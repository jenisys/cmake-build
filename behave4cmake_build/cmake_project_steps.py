# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
import os
from behave import given, when, then, step
from behave4cmake_build.cmake_build_util import make_cmake_project
from path import Path

# -----------------------------------------------------------------------------
# ASSERTIONS
# -----------------------------------------------------------------------------
def assert_cmake_project_is_initialized(cmake_project):
    if not cmake_project.initialized:
        cmake_project.diagnose_initialized_problems()
    assert cmake_project.initialized, \
        "ENSURE: cmake_project=%s is initialized (%s, cwd=%s)" % \
            (cmake_project.project_dir.relpath(), cmake_project.project_dir, Path.getcwd())


def assert_cmake_project_is_not_initialized(cmake_project):
    if cmake_project.initialized:
        cmake_project.diagnose_initialized_problems()
    assert not cmake_project.initialized, \
        "ENSURE: cmake_project=%s is not initialized (%s, cwd=%s)" % \
            (cmake_project.project_dir.relpath(), cmake_project.project_dir, Path.getcwd())


def assert_cmake_project_with_build_config_is_initialized(cmake_project, build_config):
    assert build_config, "ENSURE: build_config is not None (%s)" % build_config
    if cmake_project.config.name != build_config:
        # -- CMAKE PROJECT VARIANT: With OTHER build_config
        cmake_project = make_cmake_project(None, cmake_project.project_dir, build_config)
    assert_cmake_project_is_initialized(cmake_project)

def assert_cmake_project_with_build_config_is_not_initialized(cmake_project, build_config):
    assert build_config, "ENSURE: build_config is not None (%s)" % build_config
    if cmake_project.config.name != build_config:
        # -- CMAKE PROJECT VARIANT: With OTHER build_config
        cmake_project = make_cmake_project(None, cmake_project.project_dir, build_config)
    assert_cmake_project_is_not_initialized(cmake_project)

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def get_default_build_config(ctx=None):
    build_config = None
    if ctx:
        build_config = getattr(ctx, "cmake_default_build_config", None)
    if not build_config:
        build_config = os.environ.get("CMAKE_BUILD_CONFIG", "debug")
    return build_config

def get_last_or_default_build_config(ctx=None):
    build_config = None
    if ctx:
        build_config = getattr(ctx, "cmake_build_config", None)
    if not build_config:
        build_config = get_default_build_config(ctx)
    return build_config

def make_current_cmake_project_and_store_in_context(ctx, project_dir, build_config):
    workdir = Path(ctx.workdir or ".")
    workpath_project_dir = workdir/project_dir
    cmake_current_project = make_cmake_project(None, workpath_project_dir,
                                                   build_config=build_config)
    ctx.cmake_current_project = cmake_current_project
    # -- REMEMBER: LAST BUILD_CONFIG used
    ctx.cmake_build_config = cmake_current_project.config.name


# -----------------------------------------------------------------------------
# STEPS
# -----------------------------------------------------------------------------
@step(u'I use the CMake project "{project_dir}" with build_config="{build_config}"')
def step_i_use_cmake_project_with_build_config(ctx, project_dir, build_config):
    make_current_cmake_project_and_store_in_context(ctx, project_dir, build_config)
    # -- REMEMBER: LAST BUILD_CONFIG used
    ctx.cmake_build_config = build_config

@step(u'I use the CMake project "{project_dir}"')
def step_i_use_cmake_project(ctx, project_dir):
    build_config = get_last_or_default_build_config(ctx)
    step_i_use_cmake_project_with_build_config(ctx, project_dir, build_config=build_config)


@given(u'the CMake project is initialized')
@then(u'the CMake project is initialized')
def step_then_cmake_project_is_initialized(ctx):
    assert ctx.cmake_current_project is not None, "ENSURE: ctx.cmake_current_project exists"
    assert_cmake_project_is_initialized(ctx.cmake_current_project)

@given(u'the CMake project is not initialized')
@then(u'the CMake project is not initialized')
def step_then_cmake_project_is_not_initialized(ctx):
    assert ctx.cmake_current_project is not None, "ENSURE: ctx.cmake_current_project exists"
    assert_cmake_project_is_not_initialized(ctx.cmake_current_project)


@then(u'the CMake project is initialized with build_config="{build_config}"')
@then(u'the CMake project is initialized for build_config="{build_config}"')
@then(u'the CMake project for build_config="{build_config}" is initialized')
def step_then_cmake_project_with_build_config_is_initialized(ctx, build_config):
    assert ctx.cmake_current_project is not None, "ENSURE: ctx.cmake_current_project exists"
    assert_cmake_project_with_build_config_is_initialized(ctx.cmake_current_project, build_config)
    ctx.cmake_build_config = build_config   # REMEMBER: Last build_config

@then(u'the CMake project is not initialized for build_config="{build_config}"')
@then(u'the CMake project for build_config="{build_config}" is not initialized')
def step_then_cmake_project_with_build_config_is_not_initialized(ctx, build_config):
    assert ctx.cmake_current_project is not None, "ENSURE: ctx.cmake_current_project exists"
    assert_cmake_project_with_build_config_is_not_initialized(ctx.cmake_current_project, build_config)
    ctx.cmake_build_config = build_config   # REMEMBER: Last build_config
