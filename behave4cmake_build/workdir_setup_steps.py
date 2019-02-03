# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
from behave import given, when, then, step
from behave4cmake_build.cmake_build_util import make_cmake_project
from behave4cmd0.command_util import ensure_workdir_exists
from path import Path

@step(u'I copy the directory "{source_dir}" to the working directory "{dest_dir}"')
def step_copytree_to_workdir_with_destdir(ctx, source_dir, dest_dir):
    ensure_workdir_exists(ctx)
    workdir = Path(ctx.workdir or "__WORKDIR__").normpath()
    source_dir = Path(source_dir).normpath()
    dest_dir = Path(dest_dir).normpath()
    workpath_dest_dir = workdir/Path(dest_dir)

    assert source_dir.isdir(), "ENSURE: source_dir=%s exists" % source_dir
    workpath_dest_dir.rmtree_p()
    source_dir.copytree(workpath_dest_dir)
    assert workpath_dest_dir.isdir()


@step(u'I copy the directory "{source_dir}" to the working directory')
def step_copytree_to_workdir(ctx, source_dir):
    """Copy a directory :param:`source_dir` -> workdir:basename(source_dir)/"""
    ensure_workdir_exists(ctx)
    source_dir = Path(source_dir).normpath()
    dest_dir = source_dir.basename()
    step_copytree_to_workdir_with_destdir(ctx, source_dir, dest_dir)


@given(u'I copy the CMake project "{cmake_project_dir}" to the working directory "{dest_dir}"')
def step_given_i_copy_cmake_project_to_workdir(ctx, cmake_project_dir, dest_dir):
    step_copytree_to_workdir_with_destdir(ctx, cmake_project_dir, dest_dir)


@given(u'I copy the CMake project "{cmake_project_dir}" to the working directory')
def step_given_i_copy_cmake_project_to_workdir(ctx, cmake_project_dir):
    step_copytree_to_workdir(ctx, cmake_project_dir)
    # ensure_workdir_exists(ctx)
    # workdir = Path(ctx.workdir or "__WORKDIR__")
    # project_dir = Path(cmake_project_dir)
    # assert project_dir.isdir(), "ENSURE: directory=%s exists" % project_dir
    # workpath_project_dir = workdir/project_dir.normpath().basename()
    # workpath_project_dir.rmtree_p()
    # project_dir.copytree(workpath_project_dir)
    # assert workpath_project_dir.isdir()
    #
    # # -- DIAGNOSTICS:
    # print("PROJECT_DIR: %s" % project_dir)
    # print("WORKPATH_PROJECT_DIR: %s" % workpath_project_dir)
