# -*- coding: UTF-8 -*-
"""
Unit tests for :class:`cmake_build.model.CMakeBuildRunner` that inspect
the result CMake command-line.
"""

from __future__ import absolute_import, print_function
from collections import OrderedDict
from cmake_build.model import CMakeProject, CMakeBuildRunner
from cmake_build.config import BuildConfig
from cmake_build.cmake_util import CMAKE_GENERATOR_ALIAS_MAP
from path import Path
from invoke.util import cd
import pytest

from .test_model_project_cmake_cmdline import CMakeProjectFactory
from .test_model_project_cmake_cmdline import AbstractTestCMakeProject_WithoutParams
from .test_model_project_cmake_cmdline import AbstractTestCMakeProject_WithParam_cmake_generator
from .test_model_project_cmake_cmdline import AbstractTestCMakeProject_WithParam_config
from .test_model_project_cmake_cmdline import AbstractTestCMakeProject_WithConan


# ---------------------------------------------------------------------------
# CONSTANTS:
# ---------------------------------------------------------------------------
# class Undefined(object): pass
# UNDEFINED = Undefined()

class CMakeBuildRunnerAsCMakeProject(CMakeBuildRunner):
    """Use CMakeBuildRunner as workhorse but look like a CMakeProject instance."""
    def __init__(self, cmake_project, target=None):
        cmake_projects = [cmake_project]
        CMakeBuildRunner.__init__(self, cmake_projects, target=target)
        self._cmake_project = cmake_project

    # -- SUPPORT: CMakeProject API
    @property
    def project_dir(self):
        return self._cmake_project.project_dir

    @property
    def project_build_dir(self):
        return self._cmake_project.project_build_dir

    @property
    def ctx(self):
        return self._cmake_project.ctx

    def needs_conan(self):
        return self._cmake_project.needs_conan()

    def redo(self, *args, **kwargs):
        return self._cmake_project.redo(*args, **kwargs)

    # def __getattr__(self, name):
    #     value = getattr(self._cmake_project, name, UNDEFINED)
    #     if value is UNDEFINED:
    #         raise AttributeError(name)
    #     return value


# -------------------------------------------------------------------------
# TEST SUPPORT
# -------------------------------------------------------------------------
# -- BUILDER-FUNCTION FOR: CMakeBuildRunner as CMakeProject
class CMakeBuildRunnerAsCMakeProjectFactory(CMakeProjectFactory):
    """Wrap created CMakeProject objet(s) with a CMakeBuildRunner
    to be able to reuse abstract test suite for CMakeProject(s).
    """

    @staticmethod
    def make_newborn(tmpdir, cmake_generator=None, cmake_build_type=None, **kwargs):
        """Create NEW-BORN CMake project without build-directory."""
        cmake_project = CMakeProjectFactory.make_newborn(tmpdir,
                                cmake_generator=cmake_generator,
                                cmake_build_type=cmake_build_type,
                                 **kwargs)
        return CMakeBuildRunnerAsCMakeProject(cmake_project)

    @classmethod
    def make_initialized(cls, tmpdir, cmake_generator=None, cmake_build_type=None, **kwargs):
        """Create initialized CMake project (with build-directory)."""
        cmake_project = CMakeProjectFactory.make_initialized(tmpdir,
                                cmake_generator=cmake_generator,
                                cmake_build_type=cmake_build_type,
                                **kwargs)
        return CMakeBuildRunnerAsCMakeProject(cmake_project)


# -------------------------------------------------------------------------
# TESTS FOR: CMakeBuildRunner as CMakeProject -- Parameter Tests and Impact on CMake Command-Line
# -------------------------------------------------------------------------
# HINT: Reuse existing tests for CMakeProject by overriding CMAKE_PROJECT_FACTORY
class TestCMakeBuildRunner_WithoutParams(AbstractTestCMakeProject_WithoutParams):
    """Test CMakeBuildRunner with CMakeProject commands without any params and
    ensure that CMake command-line is correct / as expected.
    """
    CMAKE_PROJECT_FACTORY = CMakeBuildRunnerAsCMakeProjectFactory


class TestCMakeBuildRunner_WithParam_cmake_generator(AbstractTestCMakeProject_WithParam_cmake_generator):
    """Test CMakeBuildRunner with CMakeProject commands
    cmake_generator param (cmake -G <CMAKE_GENERATOR> option)
    and ensure that CMake command-line is correct.
    """
    CMAKE_PROJECT_FACTORY = CMakeBuildRunnerAsCMakeProjectFactory


class TestCMakeBuildRunner_WithParam_config(AbstractTestCMakeProject_WithParam_config):
    """Test CMakeBuildRunner with CMakeProject commands
    with config param (cmake --config option)
    and ensure that CMake command-line is correct.
    """
    CMAKE_PROJECT_FACTORY = CMakeBuildRunnerAsCMakeProjectFactory


class TestCMakeBuildRunner_WithConan(AbstractTestCMakeProject_WithConan):
    """Test CMakeBuildRunner with CMakeProject commands
    with conan support and ensure that CMake command-line is correct.
    """
    CMAKE_PROJECT_FACTORY = CMakeBuildRunnerAsCMakeProjectFactory
