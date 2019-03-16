#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
Simple example how invoke.Program can be used in own scripts/commands.

.. seealso::

    * http://docs.pyinvoke.org/en/1.2/api/program.htm
    * http://docs.pyinvoke.org/
    * http://pyinvoke.org/
"""

from __future__ import absolute_import, print_function
import os
import sys
from invoke import Program, Collection
from invoke.config import Config, merge_dicts


# ---------------------------------------------------------------------------
# CMAKE-BUILD TASKS:
# ---------------------------------------------------------------------------
from cmake_build import tasks as cmake_build_tasks
from cmake_build.tasklet import cleanup
from cmake_build.version import VERSION

namespace = Collection.from_module(cmake_build_tasks)
namespace.add_collection(Collection.from_module(cleanup))
namespace.configure(cleanup.namespace.configuration())
cleanup.cleanup_tasks.add_task(cleanup.clean_python)

if sys.platform.startswith("win"):
    # -- OVERRIDE SETTINGS: For platform=win32, ... (Windows)
    namespace.configure({"run": dict(echo=True, pty=False)})
else:
    namespace.configure({"run": dict(echo=True, pty=True)})


# ---------------------------------------------------------------------------
# CMAKE-BUILD CONFIG ENV-ALIASES:
# ---------------------------------------------------------------------------
def setup_environment_aliases4cmake_build():
    BUILD_CONFIG1 = os.environ.get("CMAKE_BUILD_CONFIG", None)
    BUILD_CONFIG2 = os.environ.get("CMAKE_BUILD_BUILD_CONFIG", None)
    if BUILD_CONFIG1 and not BUILD_CONFIG2:
        # -- SIMPLIFY USE: CMAKE_BUILD_CONFIG <=> CMAKE_BUILD_BUILD_CONFIG
        os.environ["CMAKE_BUILD_BUILD_CONFIG"] = BUILD_CONFIG1


# ---------------------------------------------------------------------------
# CMAKE-BUILD INVOKE PROGRAM:
# ---------------------------------------------------------------------------
# -- ENSURE: Use --config="cmake_build.yaml" (per default)
#   os.environ["INVOKE_RUNTIME_CONFIG"] = "cmake_build.yaml"
class CMakeBuildProgramConfig(Config):
    prefix = "cmake_build"
    file_prefix = "cmake_build"
    # env_prefix = "CMAKE_BUILD"

    def __init__(self, **kwargs):
        # -- ENSURE: Can use config="cmake_build.yaml" (via: system_prefix)
        kwargs["system_prefix"] = "./"
        super(CMakeBuildProgramConfig, self).__init__(**kwargs)

    @staticmethod
    def global_defaults():
        their_defaults = Config.global_defaults()
        my_defaults = {
            "run": {
                # "config": "cmake_build.yaml",
                "echo": True,
            },
        }
        return merge_dicts(their_defaults, my_defaults)


# class CMakeBuildProgram(Program):
#     """cmake-build, a thin wrapper around CMake to simplify using CMake.
#     Makes CMake to a build system that retrieves its configuration from
#     a configuration file ("cmake-build.yaml").
#     """
#     name = "cmake-build"
#     version = "0.1.0"
#
#     def __init__(self, **kwargs):
#         cmake_build_namespace = kwargs.pop("namespace", namespace)
#         super(CMakeBuildProgram, self).__init__(version=self.version,
#                         name=self.name,
#                         namespace=cmake_build_namespace,
#                         config_class=CMakeBuildProgramConfig,
#                         **kwargs)


# program = CMakeBuildProgram()
setup_environment_aliases4cmake_build()
program = Program(version=VERSION, namespace=namespace,
                  name="cmake-build", binary="cmake-build",
                  config_class=CMakeBuildProgramConfig)


# ---------------------------------------------------------------------------
# AUTO-MAIN:
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(program.run())
