# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
from behave import given, when, then, step
from behave4cmake_build.cmake_build_util import make_cmake_project
from path import Path


@step(u'I use the CMake project "{project_dir}" with build_config="{build_config}"')
def step_i_use_cmake_project_with_build_config(ctx, project_dir, build_config=None):
    workdir = Path(ctx.workdir or ".")
    workpath_project_dir = workdir/project_dir
    ctx.cmake_current_project = make_cmake_project(None, workpath_project_dir,
                                                   build_config=build_config)


@step(u'I use the CMake project "{project_dir}"')
def step_i_use_cmake_project(ctx, project_dir):
    step_i_use_cmake_project_with_build_config(ctx, project_dir)


@then(u'the CMake project is initialized')
def step_then_cmake_project_is_initialized(ctx):
    assert ctx.cmake_current_project is not None, "ENSURE: ctx.cmake_current_project exists"
    cmake_current_project = ctx.cmake_current_project
    assert cmake_current_project.initialized, \
        "ENSURE: cmake_project=%s is initialized" % cmake_current_project.project_dir.relpath()

@then(u'the CMake project is not initialized')
def step_then_cmake_project_is_not_initialized(ctx):
    assert ctx.cmake_current_project is not None, "ENSURE: ctx.cmake_current_project exists"
    cmake_current_project = ctx.cmake_current_project
    assert not cmake_current_project.initialized, \
        "ENSURE: cmake_project=%s is not initialized" % cmake_current_project.project_dir.relpath()


@then(u'the CMake project for build_config="{build_config}" is initialized')
def step_then_cmake_project_with_build_config_is_initialized(ctx, build_config):
    step_then_cmake_project_is_initialized(ctx)
    assert ctx.cmake_current_project.build_config.name == build_config
