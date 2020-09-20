# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
from collections import OrderedDict
from cmake_build.model import CMakeProject
from cmake_build.config import CMakeProjectPersistConfig, BuildConfig
from cmake_build.cmake_util import CMAKE_GENERATOR_ALIAS_MAP
from path import Path
from invoke.util import cd
import pytest

# ---------------------------------------------------------------------------
# CONSTANTS:
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# TESTS SUPPORT:
# ---------------------------------------------------------------------------
class MockContext(object):
    def __init__(self, config=None):
        self.config = config or {}
        self.runlog = []

    def clear(self):
        self.runlog = []

    @property
    def commands(self):
        return self.runlog

    @property
    def last_command(self):
        if not self.runlog:
            return None
        return self.runlog[-1]

    def run(self, cmdline, result=0, sideeffect=None):
        self.runlog.append(cmdline)
        if sideeffect:
            sideeffect()
        return result



# -------------------------------------------------------------------------
# TEST SUPPORT
# -------------------------------------------------------------------------
DEFAULT_CMAKE_BUILD_TYPE = "Debug"
DEFAULT_CMAKE_GENERATOR = "ninja"

class CMakeProjectFactory(object):
    @staticmethod
    def make_newborn(tmpdir, cmake_generator=None, cmake_build_type=None):
        """Create NEW-BORN CMake project without build-directory."""
        cmake_generator = cmake_generator or DEFAULT_CMAKE_GENERATOR
        cmake_build_type = cmake_build_type or DEFAULT_CMAKE_BUILD_TYPE
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator=cmake_generator,
                                cmake_build_type=cmake_build_type)
        assert not project_build_dir.isdir()

        # -- STEP 1: First cmake_project.init
        with cd(project_dir):
            cmake_project = CMakeProject(ctx, project_dir, project_build_dir, build_config)
            return cmake_project

    @classmethod
    def make_initialized(cls, tmpdir, cmake_generator=None, cmake_build_type=None):
        """Create initialized CMake project (with build-directory)."""
        cmake_project = cls.make_newborn(tmpdir,
                                        cmake_generator=cmake_generator,
                                        cmake_build_type=cmake_build_type)
        with cd(cmake_project.project_dir):
            cmake_project.init()
            assert cmake_project.initialized
        return cmake_project


# -------------------------------------------------------------------------
# ABSTRACT TEST SUITE FOR: CMakeProject -- Parameter Tests and Impact on CMake Command-Line
# -------------------------------------------------------------------------
class AbstractCMakeProjectTest(object):
    CMAKE_PROJECT_FACTORY = CMakeProjectFactory

    # -- COMMON BUILDER-FUNCTION FOR: CMakeProject
    @classmethod
    def make_newborn_cmake_project(cls, tmpdir, cmake_generator=None, **kwargs):
        cmake_project_factory = cls.CMAKE_PROJECT_FACTORY
        cmake_project = cmake_project_factory.make_newborn(tmpdir,
                                    cmake_generator=cmake_generator,
                                    **kwargs)
        return cmake_project

    @classmethod
    def make_initialized_cmake_project(cls, tmpdir, cmake_generator=None, **kwargs):
        cmake_project_factory = cls.CMAKE_PROJECT_FACTORY
        cmake_project = cmake_project_factory.make_initialized(tmpdir,
                                    cmake_generator=cmake_generator,
                                    **kwargs)
        return cmake_project

class AbstractTestCMakeProject_WithoutParams(AbstractCMakeProjectTest):
    """Test CMakeProject commands without any params and ensure that
    CMake command-line is correct / as expected.
    """
    CONFIGURATIONS = ["Debug", "Release"]

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_init(self, tmpdir, config):
        cmake_project = self.make_newborn_cmake_project(tmpdir,
                                               cmake_generator="ninja",
                                               cmake_build_type=config)
        with cd(cmake_project.project_dir):
            cmake_project.init()

        expected = "cmake -G Ninja -DCMAKE_BUILD_TYPE={0} ..".format(config)
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_build(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir,
                                                cmake_generator="ninja",
                                                cmake_build_type=config)
        with cd(cmake_project.project_dir):
            cmake_project.build()

        expected = "cmake --build ."
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_ctest(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir,
                                cmake_generator="ninja",
                                cmake_build_type=config)
        with cd(cmake_project.project_dir):
            cmake_project.test()

        expected = "ctest"
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_install(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir,
                                cmake_generator="ninja",
                                cmake_build_type=config)
        with cd(cmake_project.project_dir):
            cmake_project.install()

        expected = "cmake --build .  --target install"
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_pack(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir,
                                cmake_generator="ninja",
                                cmake_build_type=config)
        with cd(cmake_project.project_dir):
            cmake_project.pack()

        expected = "cpack -G ZIP --config CPackConfig.cmake"
        last_command = cmake_project.ctx.last_command
        assert last_command == expected
        assert config not in last_command

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_clean(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir,
                                cmake_generator="ninja",
                                cmake_build_type=config)
        with cd(cmake_project.project_dir):
            cmake_project.clean()

        expected = "cmake --build .  -- clean"
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_rebuild(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir,
                                cmake_generator="ninja",
                                cmake_build_type=config)
        cmake_project.ctx.clear()
        with cd(cmake_project.project_dir):
            cmake_project.rebuild()

        expected = [
            "cmake --build .  -- clean",
            "cmake --build ."
        ]
        assert cmake_project.ctx.commands == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_redo(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir,
                                cmake_generator="ninja",
                                cmake_build_type=config)
        cmake_project.ctx.clear()
        with cd(cmake_project.project_dir):
            cmake_project.redo()

        expected = [
            "cmake -G Ninja -DCMAKE_BUILD_TYPE={0} ..".format(config),
            "cmake --build .  -- clean",
            "cmake --build .",
        ]
        assert cmake_project.ctx.commands == expected


class AbstractTestCMakeProject_WithParam_cmake_generator(AbstractCMakeProjectTest):
    """Test CMakeProject commands with cmake_generator param (cmake -G <CMAKE_GENERATOR> option)
    and ensure that CMake command-line is correct.
    """
    CMAKE_GENERATORS = ["make", "ninja", "ninja.multi", "ninja-multi"]

    @pytest.mark.parametrize("cmake_generator, generator_name", [
        ("make", '"Unix Makefiles"'),
        ("ninja", "Ninja"),
        ("Ninja", "Ninja"),
        ("ninja.multi", '"Ninja Multi-Config"'),
        ("ninja-multi", '"Ninja Multi-Config"'),
    ])
    def test_init(self, tmpdir, cmake_generator, generator_name):
        generator_name2 = CMAKE_GENERATOR_ALIAS_MAP.get(cmake_generator, cmake_generator)
        cmake_project = self.make_newborn_cmake_project(tmpdir, cmake_generator=cmake_generator)
        with cd(cmake_project.project_dir):
            cmake_project.init()

        name_needs_quoting = generator_name.count(" ") > 0
        expected = "cmake -G {0} -DCMAKE_BUILD_TYPE=Debug ..".format(generator_name)
        assert cmake_project.ctx.last_command == expected
        assert generator_name.replace('"', "") == generator_name2
        if name_needs_quoting:
            assert cmake_project.ctx.last_command.count('"') == 2


class AbstractTestCMakeProject_WithParam_config(AbstractCMakeProjectTest):
    """Test CMakeProject commands with config param (cmake --config option)
    and ensure that CMake command-line is correct.
    """
    CONFIGURATIONS = ["Debug", "Release"]

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_init(self, tmpdir, config):
        cmake_project = self.make_newborn_cmake_project(tmpdir, cmake_generator="ninja")
        with cd(cmake_project.project_dir):
            cmake_project.init(config=config)

        expected = "cmake -G Ninja --config {0} -DCMAKE_BUILD_TYPE={0} ..".format(config)
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_build(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir, cmake_generator="ninja")
        with cd(cmake_project.project_dir):
            cmake_project.build(config=config)

        expected = "cmake --build . --config {0}".format(config)
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_ctest(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir, cmake_generator="ninja")
        with cd(cmake_project.project_dir):
            cmake_project.test(config=config)

        expected = "ctest -C {0}".format(config)
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_install(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir, cmake_generator="ninja")
        with cd(cmake_project.project_dir):
            cmake_project.install(config=config)

        expected = "cmake --build . --config {0} --target install".format(config)
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_pack(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir, cmake_generator="ninja")
        with cd(cmake_project.project_dir):
            cmake_project.pack(config=config)

        expected = "cpack -G ZIP --config CPackConfig.cmake"
        last_command = cmake_project.ctx.last_command
        assert last_command == expected
        assert config not in last_command

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_clean(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir, cmake_generator="ninja")
        with cd(cmake_project.project_dir):
            cmake_project.clean(config=config)

        expected = "cmake --build . --config {0} -- clean".format(config)
        assert cmake_project.ctx.last_command == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_rebuild(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir, cmake_generator="ninja")
        cmake_project.ctx.clear()
        with cd(cmake_project.project_dir):
            cmake_project.rebuild(config=config)

        expected = [
            "cmake --build . --config {0} -- clean".format(config),
            "cmake --build . --config {0}".format(config),
        ]
        assert cmake_project.ctx.commands == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_redo(self, tmpdir, config):
        cmake_project = self.make_initialized_cmake_project(tmpdir, cmake_generator="ninja")
        cmake_project.ctx.clear()
        with cd(cmake_project.project_dir):
            cmake_project.redo(config=config)

        expected = [
            "cmake -G Ninja --config {0} -DCMAKE_BUILD_TYPE={0} ..".format(config),
            "cmake --build . --config {0} -- clean".format(config),
            "cmake --build . --config {0}".format(config),
        ]
        assert cmake_project.ctx.commands == expected

class AbstractTestCMakeProject_WithConan(AbstractCMakeProjectTest):
    """Test CMakeProject that uses "conan" (only basic support provided).
    Ensure that on CMake project init:

    * conan setup is performed
    * CMake command-line is correct (for CMakeProject.init)
    """
    CONFIGURATIONS = ["Debug", "Release"]
    CONAN_FILES = ["conanfile.py", "conanfile.txt"]

    def make_cmake_conan_project(self, cmake_project, conanfile=None):
        conanfile = conanfile or "conanfile.py"
        conanfile_path = cmake_project.project_dir/conanfile
        if not conanfile_path.exists():
            conanfile_path.write_text("# CONAN: conanfile.py")
        assert conanfile_path.exists()

    @pytest.mark.parametrize("conanfile", CONAN_FILES)
    def test_needs_conan(self, tmpdir, conanfile):
        cmake_project = self.make_newborn_cmake_project(tmpdir, cmake_generator="ninja")
        self.make_cmake_conan_project(cmake_project, conanfile=conanfile)
        assert cmake_project.needs_conan()

    @pytest.mark.parametrize("conanfile", CONAN_FILES)
    def test_init(self, tmpdir, conanfile):
        cmake_build_type = "Debug"
        cmake_project = self.make_newborn_cmake_project(tmpdir,
                                               cmake_generator="ninja",
                                               cmake_build_type=cmake_build_type)
        self.make_cmake_conan_project(cmake_project, conanfile=conanfile)
        assert cmake_project.needs_conan()
        with cd(cmake_project.project_dir):
            cmake_project.init()

        expected = [
            "conan install .. -s build_type={0}".format(cmake_build_type),
            "cmake -G Ninja -DCMAKE_BUILD_TYPE={0} ..".format(cmake_build_type),
        ]
        assert cmake_project.ctx.commands == expected

    @pytest.mark.parametrize("cmake_build_type", CONFIGURATIONS)
    def test_init_with_cmake_build_type(self, tmpdir, cmake_build_type):
        cmake_project = self.make_newborn_cmake_project(tmpdir, cmake_generator="ninja",
                                               cmake_build_type=cmake_build_type)
        self.make_cmake_conan_project(cmake_project, conanfile="conanfile.py")
        assert cmake_project.needs_conan()
        with cd(cmake_project.project_dir):
            cmake_project.init()

        expected = [
            "conan install .. -s build_type={0}".format(cmake_build_type),
            "cmake -G Ninja -DCMAKE_BUILD_TYPE={0} ..".format(cmake_build_type),
        ]
        assert cmake_project.ctx.commands == expected

    @pytest.mark.parametrize("config", CONFIGURATIONS)
    def test_init_with_config(self, tmpdir, config):
        cmake_project = self.make_newborn_cmake_project(tmpdir, cmake_generator="ninja",
                                               cmake_build_type=config)
        self.make_cmake_conan_project(cmake_project, conanfile="conanfile.py")
        assert cmake_project.needs_conan()
        with cd(cmake_project.project_dir):
            cmake_project.init(config=config)

        expected = [
            "conan install .. -s build_type={0}".format(config),
            "cmake -G Ninja --config {0} -DCMAKE_BUILD_TYPE={0} ..".format(config),
        ]
        assert cmake_project.ctx.commands == expected


# -------------------------------------------------------------------------
# TESTS FOR: CMakeProject -- Parameter Tests and Impact on CMake Command-Line
# -------------------------------------------------------------------------
class TestCMakeProject_WithoutParams(AbstractTestCMakeProject_WithoutParams):
    CMAKE_PROJECT_FACTORY = CMakeProjectFactory

class TestCMakeProject_WithParam_cmake_generator(AbstractTestCMakeProject_WithParam_cmake_generator):
    CMAKE_PROJECT_FACTORY = CMakeProjectFactory

class TestCMakeProject_WithConan(AbstractTestCMakeProject_WithConan):
    CMAKE_PROJECT_FACTORY = CMakeProjectFactory
class TestCMakeProject_WithParam_config(AbstractTestCMakeProject_WithParam_config):
    CMAKE_PROJECT_FACTORY = CMakeProjectFactory
