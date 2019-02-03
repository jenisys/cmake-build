# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
from cmake_build.model import CMakeProject, BuildConfig
from cmake_build import tasks # make_cmake_project,  make_build_config
from path import Path


class MockConfig(object):
    defaults = {
        "build_configs": dict(debug={}, release={}),
        "build_config_aliases": {
            "default": "debug"
        },
        "projects": []
    }

    def __init__(self, data=None, **kwargs):
        self.data = {}
        self.data.update(self.defaults)
        if data:
            self.data.update(data)
        self.data.update(**kwargs)
        self.build_dir_schema = "build.{BUILD_CONFIG}"
        self.build_config = self.build_config_aliases.get("default", "debug")
        self.cmake_generator = "ninja"
        self.cmake_toolchain = None

    @property
    def build_configs(self):
        return self.data["build_configs"]

    @property
    def build_config_aliases(self):
        return self.data["build_config_aliases"]

    @property
    def build_projects(self):
        return self.data["projects"]


class MockContext(object):
    def __init__(self, config=None, **kwargs):
        self.config = MockConfig(config, **kwargs)

    def run(self, args, **kwargs):
        return NotImplemented


def make_context_object(workdir=None):
    return MockContext()


def make_build_config(ctx, build_config=None):
    if ctx is None:
        ctx = make_context_object()
    return tasks.make_build_config(ctx, build_config)


def make_cmake_project(ctx, project_dir, build_config=None, **kwargs):
    if ctx is None:
        ctx = make_context_object()
    # build_config_data = make_build_config(ctx, build_config)
    # cmake_project = CMakeProject(ctx, project_dir, build_config=build_config_data)
    # return cmake_project
    return tasks.make_cmake_project(ctx, project_dir, build_config=build_config, **kwargs)


def make_simple_cmake_project(project_dir, build_config=None, **kwargs):
    ctx = make_context_object()
    return make_cmake_project(ctx, project_dir, build_config=build_config, **kwargs)
