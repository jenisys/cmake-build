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
from distutils.util import strtobool
from pathlib import Path
from invoke import Program, Collection
from invoke.config import Config, merge_dicts

# ---------------------------------------------------------------------------
# CONSTANTS:
# ---------------------------------------------------------------------------
USE_PYTHON_CLEANUP = os.environ.get("CMAKE_BUILD_CLEANUP_PYTHON", "no") == "yes"


# ---------------------------------------------------------------------------
# CMAKE-BUILD TASKS:
# ---------------------------------------------------------------------------
from cmake_build import tasks as cmake_build_tasks
from cmake_build.tasklet import cleanup
from cmake_build.version import VERSION

namespace = Collection.from_module(cmake_build_tasks)
namespace.add_collection(Collection.from_module(cleanup))
namespace.configure(cleanup.namespace.configuration())
if USE_PYTHON_CLEANUP:
    # -- OPTIONAL PART:
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
        config_file = self.locate_config_file()
        kwargs["system_prefix"] = self.select_system_prefix(config_file)
        super(CMakeBuildProgramConfig, self).__init__(**kwargs)
        self._config_file = config_file
        if config_file and config_file.parent != Path.cwd():
            # -- SPECIAL CASE: Disable any projects and store current location
            # DISABLED: self.load_basedir_config(config_file)
            self["projects"] = []
            self["project_location"] = str(Path.cwd())

        # -- REMEMBER: Which config-file is used and where it is.
        # NEEDED-FOR: Relative path normalization.
        if config_file:
            self["config_file"] = str(config_file)
            self["config_dir"] = str(config_file.parent)
        else:
            self["config_file"] = None
            self["config_dir"] = "."


    @classmethod
    def locate_config_file(cls):
        """Hunt for config-file in current working directory (cwd) and upword."""
        cwd = Path.cwd()
        config_filename = Path("{0}.yaml".format(cls.file_prefix))
        config_file = cwd/config_filename
        if config_file.exists():
            return config_file

        # -- MAYBE: INHERIT CONFIG-FILE FROM BASE DIRECTORY (walk towards root-dir)
        inherits_config_file = strtobool(
            os.environ.get("CMAKE_BUILD_INHERIT_CONFIG_FILE", "yes"))
        if inherits_config_file and not config_file.exists():
            for base_dir in cwd.parents:
                config_file = base_dir/config_filename
                if config_file.exists():
                    return config_file
        # -- OTHERWISE: NOT-FOUND
        return None

    @classmethod
    def select_system_prefix(cls, config_file=None):
        if not config_file:
            config_file = cls.locate_config_file()
        system_prefix = "."
        if config_file:
            config_relpath = os.path.relpath(str(config_file), str(Path.cwd()))
            parent_relpath = os.path.relpath(str(config_file.parent), str(Path.cwd()))
            annotation = "as CONFIG"
            if parent_relpath != ".":
                annotation = "for DEFAULTS"
            print("CMAKE-BUILD: Using {0} ({1})".format(config_relpath, annotation))
            system_prefix = str(config_file.parent)
            # system_prefix = parent_relpath

        if not system_prefix.endswith("/"):
            system_prefix = "{0}/".format(system_prefix)
        # print("SELECT-CONFIG-FILE: system_prefix={0}".format(system_prefix))
        return system_prefix

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
