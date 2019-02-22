# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
import os
from cmake_build import model_builder


class MockConfig(object):
    defaults = {
        "build_config": os.environ.get("CMAKE_BUILD_CONFIG", "debug"),
        "build_configs": ["debug", "release"],
        "projects": [],
        # DISABLED: "build_config_aliases": {"default": "debug"},
    }

    def __init__(self, data=None, **kwargs):
        self.data = {}
        self.data.update(self.defaults)
        if data:
            self.data.update(data)
        self.data.update(**kwargs)
        self.build_dir_schema = "build.{BUILD_CONFIG}"
        self.build_config = self.data.get("build_config")
        self.build_configs_map = {}
        self.cmake_generator = "ninja"
        self.cmake_toolchain = None
        # DISABLED: self.build_config = self.build_config_aliases.get("default", "debug")

    def get(self, name, default=None):
        if name == "build_configs_map":
            return self.build_configs_map
        else:
            return self.data.get(name, default)

    @property
    def build_configs(self):
        return self.data["build_configs"]

    @property
    def projects(self):
        return self.data["projects"]

    # DISABLED:
    # @property
    # def build_config_aliases(self):
    #     return self.data["build_config_aliases"]

    # XXX-JE-CHECK:
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
    return model_builder.make_build_config(ctx, build_config)


def make_cmake_project(ctx, project_dir, build_config=None, **kwargs):
    if ctx is None:
        ctx = make_context_object()
    # build_config_data = make_build_config(ctx, build_config)
    # cmake_project = CMakeProject(ctx, project_dir, build_config=build_config_data)
    # return cmake_project
    return model_builder.make_cmake_project(ctx, project_dir, build_config=build_config, **kwargs)


def make_simple_cmake_project(project_dir, build_config=None, **kwargs):
    ctx = make_context_object()
    return make_cmake_project(ctx, project_dir, build_config=build_config, **kwargs)
