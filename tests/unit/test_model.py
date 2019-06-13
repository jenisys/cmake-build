# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
from collections import OrderedDict
from cmake_build.model import \
    CMakeProject, CMakeProjectData, CMakeProjectPersistentData, BuildConfig, \
    CMAKE_CONFIG_DEFAULTS
from path import Path
from invoke.util import cd
import pytest


# ---------------------------------------------------------------------------
# CONSTANTS:
# ---------------------------------------------------------------------------
# CMAKE_PROJECT_BUILD_CONFIG_FILENAME = ".cmake_build.build_config.json"
# CMAKE_PROJECT_BUILD_CONFIG_FILENAME = CMakeProjectPersistentData.FILE_BASENAME

# -- SUPPORT EQUAL-TO COMPARISON:
CMAKE_CONFIG_DEFAULTS.update(cmake_defines=OrderedDict())


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


def assert_cmake_project_used_init_using_captured(cmake_project, captured, cmake_generator=""):
    build_dir = cmake_project.project_dir.relpathto(cmake_project.project_build_dir)
    assert "CMAKE-INIT:  {0} (using cmake.generator={1})".format(build_dir, cmake_generator) in captured.out
    # -- NOT-CONTAINED IN CAPTURED OUTPUT:
    assert "CMAKE-INIT:  {0} (SKIPPED: Initialized with cmake.generator=".format(build_dir) not in captured.out


def assert_cmake_project_used_reinit_using_captured(cmake_project, captured, cmake_generator=""):
    build_dir = cmake_project.project_dir.relpathto(cmake_project.project_build_dir)
    assert "CMAKE-INIT:  {0} (NEEDS-REINIT)".format(build_dir) in captured.out
    assert_cmake_project_used_init_using_captured(cmake_project, captured, cmake_generator)


def assert_cmake_project_used_update_using_captured(cmake_project, captured, cmake_generator=""):
    build_dir = cmake_project.project_dir.relpathto(cmake_project.project_build_dir)
    assert "CMAKE-INIT:  {0} (NEEDS-UPDATE)".format(build_dir) in captured.out
    assert "CMAKE-INIT:  {0} (using cmake.generator={1})".format(build_dir, cmake_generator) in captured.out
    # -- NOT-CONTAINED IN CAPTURED OUTPUT:
    assert "CMAKE-INIT:  {0} (NEEDS-REINIT)".format(build_dir) not in captured.out
    assert "CMAKE-INIT:  {0} (SKIPPED: Initialized with cmake.generator=".format(build_dir) not in captured.out


def assert_cmake_project_skipped_reinit_using_captured(cmake_project, captured, cmake_generator=""):
    build_dir = cmake_project.project_dir.relpathto(cmake_project.project_build_dir)
    assert "CMAKE-INIT:  {0} (SKIPPED: Initialized with cmake.generator=".format(build_dir) in captured.out
    # -- NOT-CONTAINED IN CAPTURED OUTPUT:
    assert "CMAKE-INIT:  {0} (NEEDS-REINIT)".format(build_dir) not in captured.out
    assert "CMAKE-INIT:  {0} (using cmake.generator={1})".format(build_dir, cmake_generator) not in captured.out


# ---------------------------------------------------------------------------
# TESTS FOR: CMakeProjectData
# ---------------------------------------------------------------------------
class TestCMakeProjectData(object):

    def test_ctor__without_data_contains_default_values(self):
        project_data = CMakeProjectData()
        expected = CMAKE_CONFIG_DEFAULTS.copy()
        assert len(project_data.data) > 0
        assert len(project_data.data) == len(CMAKE_CONFIG_DEFAULTS)
        assert project_data.data == expected
        assert "cmake_toolchain" in project_data
        assert "cmake_generator" in project_data
        assert "cmake_build_type" in project_data
        assert "cmake_defines" in project_data
        assert "cmake_args" in project_data

    def test_ctor__kwargs_can_override_data(self):
        data = dict(one=1)
        kwargs = dict(one=2)
        project_data = CMakeProjectData(data.copy(), **kwargs)
        # assert project_data.data != data
        assert project_data.data["one"] == kwargs["one"]
        assert project_data.data["one"] != data["one"]

    def test_ctor__kwargs_can_extend_data(self):
        data = dict(one=1)
        kwargs = dict(two=2)
        project_data = CMakeProjectData(data.copy(), **kwargs)
        initial_size = len(CMAKE_CONFIG_DEFAULTS)
        assert project_data.data != data
        assert len(project_data.data) == initial_size + 2
        assert project_data.data["one"] == 1
        assert project_data.data["two"] == 2

    @pytest.mark.parametrize("data", [
        {},
        dict(one=1),
        dict(one=1, two=2),
    ])
    def test_equals__with_same_data(self, data):
        project_data1 = CMakeProjectData(data)
        project_data2 = CMakeProjectData(data=data.copy())
        assert project_data1 == project_data2
        assert project_data1.data is not project_data2.data

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(),      dict(one=1),  "different-size"),
        (dict(one=1), dict(one=2), "same-size/keys: different-values"),
        (dict(one=1, two=2), dict(one=1, two=42), "one value differs"),
        (dict(one=1, two=2), dict(one=1, three=3), "one key/item differs"),
    ])
    def test_equals__with_other_data(self, data1, data2, case):
        project_data1 = CMakeProjectData(data1)
        project_data2 = CMakeProjectData(data2)
        assert project_data1 != project_data2, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=dict(k1=[1, 2, 3])), dict(one=dict(k1=[1, 3, 2])), "deep different-values"),
    ])
    def test_equals__with_other_data_and_deep_diff(self, data1, data2, case):
        project_data1 = CMakeProjectData(data1)
        project_data2 = CMakeProjectData(data2)
        assert project_data1 != project_data2, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=1), dict(one=1), "same_data"),
    ])
    def test_equals__can_compare_with_same_dict(self, data1, data2, case):
        project_data1 = CMakeProjectData(data1)
        data2.update(CMAKE_CONFIG_DEFAULTS)
        assert project_data1 == data2, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=1), dict(one=12), "different-values"),
    ])
    def test_equals__can_compare_with_other_dict(self, data1, data2, case):
        project_data1 = CMakeProjectData(data1)
        data2.update(CMAKE_CONFIG_DEFAULTS)
        assert project_data1 != data2, "CASE: %s" % case


# ---------------------------------------------------------------------------
# TESTS FOR: CMakeProjectPersistentData
# ---------------------------------------------------------------------------
class TestCMakeProjectPersistentData(object):

    def test_ctor__without_data_contains_defaults(self):
        project_data = CMakeProjectPersistentData()
        assert len(project_data.data) > 0
        assert project_data == CMAKE_CONFIG_DEFAULTS

    def test_ctor__kwargs_can_override_data(self):
        data = dict(one="ORIGINAL")
        project_data = CMakeProjectPersistentData(data=data, one="OTHER")
        assert project_data["one"] == "OTHER"

    def test_ctor__cmake_toolchain_can_override_data(self):
        data = dict(cmake_toolchain="ORIGINAL_TOOLCHAIN")
        project_data = CMakeProjectPersistentData(data=data,
                                                  cmake_toolchain="OTHER_TOOLCHAIN")
        assert project_data["cmake_toolchain"] == "OTHER_TOOLCHAIN"
        assert project_data.cmake_toolchain == "OTHER_TOOLCHAIN"

    def test_ctor__cmake_generator_can_override_data(self):
        data = dict(cmake_generator="ORIGINAL")
        project_data = CMakeProjectPersistentData(data=data,
                                                  cmake_generator="OTHER")
        assert project_data["cmake_generator"] == "OTHER"
        assert project_data.cmake_generator == "OTHER"

    def test_load__with_non_existent_file_provides_defaults(self, tmp_path):
        filename = tmp_path/CMakeProjectPersistentData.FILE_BASENAME
        assert not Path(filename).exists()
        project_data = CMakeProjectPersistentData.load(filename)
        assert project_data == CMAKE_CONFIG_DEFAULTS

    def test_load__with_existent_file(self, tmp_path):
        filename = Path(str(tmp_path/CMakeProjectPersistentData.FILE_BASENAME))
        filename.remove_p()
        assert not filename.exists()

        data = {
            "cmake_generator": "ninja",
            "cmake_toolchain": "cmake/toolchain/t1.cmake",
            "cmake_build_type": "Release",
        }
        project_data1 = CMakeProjectPersistentData(filename, data=data)
        project_data1.save()
        assert filename.exists()

        project_data2 = CMakeProjectPersistentData.load(filename)
        expected = CMAKE_CONFIG_DEFAULTS.copy()
        expected.update(data)
        assert project_data2 == expected
        assert project_data2 == project_data1
        assert project_data2 != CMAKE_CONFIG_DEFAULTS



# ---------------------------------------------------------------------------
# TESTS FOR: BuildConfig
# ---------------------------------------------------------------------------
class TestBuildConfig(object):
    """Test the BuildConfig

    .. code-block:: YAML

        # -- FILE: cmake_build.config.yaml
        ...
        build_configs:
          - Linux_arm64_Debug:
            - cmake_build_type: Debug
            - cmake_toolchain: cmake/toolchain/linux_gcc_arm64.cmake
            - cmake_defines:
                - CMAKE_BUILD_TYPE=Debug
            - cmake_init_args: --warn-uninitialized --check-system-vars

          - Linux_arm64_Release:
            - cmake_build_type: MinSizeRel
            - cmake_toolchain: cmake/toolchain/linux_gcc_arm64.cmake
            - cmake_generator: ninja

    """

    def test_cmake_generator__with_generator(self):
        build_config = BuildConfig(cmake_generator="foo")
        assert build_config.cmake_generator == "foo"
        assert build_config.get("cmake_generator") == "foo"
        assert build_config["cmake_generator"] == "foo"
        assert build_config.data.get("cmake_generator") == "foo"


    def test_cmake_generator__without_generator(self):
        build_config = BuildConfig()
        cmake_generator1 = build_config.get("cmake_generator", None)
        cmake_generator2 = build_config["cmake_generator"]
        assert build_config.cmake_generator is None
        assert cmake_generator1 is None
        assert cmake_generator2 is None

    def test_cmake_toolchain__with_toolchain(self):
        build_config = BuildConfig(cmake_toolchain="cmake/toolchain_1.cmake")
        assert build_config.cmake_toolchain == "cmake/toolchain_1.cmake"
        assert build_config.get("cmake_toolchain") == "cmake/toolchain_1.cmake"
        assert build_config["cmake_toolchain"] == "cmake/toolchain_1.cmake"
        assert build_config.data.get("cmake_toolchain") == "cmake/toolchain_1.cmake"

    def test_cmake_toolchain__without_toolchain(self):
        build_config = BuildConfig()
        cmake_toolchain1 = build_config.get("cmake_toolchain", None)
        cmake_toolchain2 = build_config["cmake_toolchain"]
        assert build_config.cmake_toolchain is None
        assert cmake_toolchain1 is None
        assert cmake_toolchain2 is None

    def test_cmake_defines__with_one_item(self):
        build_config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        assert list(build_config.cmake_defines.items()) == [("one", "VALUE_1")]
        assert list(build_config.get("cmake_defines").items()) == [("one", "VALUE_1")]
        assert list(build_config["cmake_defines"].items()) == [("one", "VALUE_1")]
        assert list(build_config.data.get("cmake_defines").items()) == [("one", "VALUE_1")]


    def test_cmake_defines__without_any(self):
        build_config = BuildConfig()
        assert list(build_config.cmake_defines.items()) == []
        assert list(build_config["cmake_defines"].items()) == []

    def test_cmake_defines__set(self):
        build_config = BuildConfig()
        definitions = [("one", "VALUE_1"), ("two", "VALUE_2")]
        build_config.cmake_defines = definitions
        assert list(build_config.cmake_defines.items()) == definitions
        assert list(build_config["cmake_defines"].items()) == definitions

    def test_cmake_defines_add__with_new_item_appends(self):
        build_config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        build_config.cmake_defines_add("NEW", "NEW_VALUE")
        expected = [
            ("one", "VALUE_1"),
            ("NEW", "NEW_VALUE"),
        ]
        assert list(build_config.cmake_defines.items()) == expected
        assert list(build_config["cmake_defines"].items()) == expected

    def test_cmake_defines_add__with_existing_item_overrides(self):
        build_config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        build_config.cmake_defines_add("one", "NEW_VALUE")
        expected = [("one", "NEW_VALUE")]
        assert list(build_config.cmake_defines.items()) == expected
        assert list(build_config["cmake_defines"].items()) == expected

    def test_cmake_defines_remove__with_unknown_item(self):
        build_config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        build_config.cmake_defines_remove("UNKNOWN")
        expected = [("one", "VALUE_1")]
        assert list(build_config.cmake_defines.items()) == expected
        assert list(build_config["cmake_defines"].items()) == expected

    def test_cmake_defines_add__with_existing_item_removes_it(self):
        definitions = [("one", "VALUE_1"), ("two", "VALUE_2")]
        build_config = BuildConfig(cmake_defines=definitions)
        build_config.cmake_defines_remove("two")
        expected = [("one", "VALUE_1")]
        assert list(build_config.cmake_defines.items()) == expected
        assert list(build_config["cmake_defines"].items()) == expected

    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type(self, build_config_name, expected):
        build_config = BuildConfig(build_config_name)
        cmake_build_type = build_config.derive_cmake_build_type()
        assert build_config.name == build_config_name
        assert cmake_build_type == expected

    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type_if_unconfigured(self, build_config_name, expected):
        build_config = BuildConfig(build_config_name)
        build_config.cmake_build_type = None    # -- DISABLED: default-init.
        assert build_config.name == build_config_name
        assert build_config.cmake_build_type is None, "ENSURE: No assignment"

        cmake_build_type = build_config.derive_cmake_build_type_if_unconfigured()
        assert cmake_build_type == expected
        assert build_config.cmake_build_type == expected

    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type_if_unconfigured__with_initial_value(self, build_config_name, expected):
        build_config = BuildConfig(build_config_name, cmake_build_type="INITIAL")
        assert build_config.name == build_config_name
        assert build_config.cmake_build_type == "INITIAL"

        build_config.derive_cmake_build_type_if_unconfigured()
        assert build_config.cmake_build_type == "INITIAL", "ENSURE: INITIAL value is preserved."

    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type_and_assign(self, build_config_name, expected):
        build_config = BuildConfig(build_config_name, cmake_build_type="INITIAL")
        assert build_config.name == build_config_name
        assert build_config.cmake_build_type == "INITIAL"

        cmake_build_type = build_config.derive_cmake_build_type_and_assign()
        assert cmake_build_type == expected
        assert build_config.cmake_build_type == expected


# ---------------------------------------------------------------------------
# TESTS FOR: CMakeProject
# ---------------------------------------------------------------------------
class TestCMakeProject(object):

    def test_init__init_without_build_dir(self, tmpdir):
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="NINJA")
        cmake_project = CMakeProject(ctx, project_dir, project_build_dir, build_config)
        assert not project_build_dir.isdir()

        with cd(project_dir):
            cmake_project.init()
            assert ctx.last_command == "cmake -G NINJA .."

    def test_init__skip_same_data(self, tmpdir, capsys):
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="NINJA")
        cmake_project1 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
        assert not project_build_dir.isdir()

        # -- STEP 1: First cmake_project.init
        with cd(project_dir):
            cmake_project1.init()

            # -- POSTCONDITIONS:
            cmake_build_filename = project_build_dir/CMakeProjectPersistentData.FILE_BASENAME
            assert project_build_dir.exists(), "ENSURE: project_build_dir exists"
            assert cmake_build_filename.exists()
            captured = capsys.readouterr()
            assert_cmake_project_used_init_using_captured(cmake_project1, captured,
                                                          cmake_generator="NINJA")

        # -- STEP 2: Second cmake_project.init => SKIPPED
        with cd(project_dir):
            ctx.clear()
            cmake_project2 = CMakeProject(ctx, project_dir.relpath(),
                                          project_build_dir.relpath(),
                                          build_config)
            cmake_project2.init()
            captured = capsys.readouterr()
            assert ctx.last_command is None
            assert_cmake_project_skipped_reinit_using_captured(cmake_project1, captured)

    def test_init__performs_reinit_with_other_cmake_generator(self, tmpdir, capsys):
        ctx = MockContext()
        project_dir = Path(str(tmpdir)).abspath()
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="make")
        cmake_project1 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
        assert not project_build_dir.isdir()

        # -- STEP 1: First cmake_project.init
        with cd(project_dir):
            cmake_project1.init()

            # -- POSTCONDITIONS:
            cmake_build_filename = project_build_dir/CMakeProjectPersistentData.FILE_BASENAME
            assert project_build_dir.exists(), "ENSURE: project_build_dir exists"
            assert cmake_build_filename.exists()
            captured = capsys.readouterr()
            assert_cmake_project_used_init_using_captured(cmake_project1, captured,
                                                          cmake_generator="make")
            # assert "CMAKE-INIT:  build (using cmake.generator=make)" in captured.out
            assert ctx.last_command == 'cmake -G "Unix Makefiles" ..'

        # -- STEP 2: Second cmake_project.init => REINIT: Other cmake_generator is used.
        with cd(project_dir):
            ctx.clear()
            # build_config.cmake_generator = "ninja"
            cmake_project2 = CMakeProject(ctx, project_dir.relpath(),
                                          project_build_dir.relpath(), build_config,
                                          cmake_generator="ninja")
            assert cmake_project2.needs_reinit(), "ENSURE: Need for reinit"
            cmake_project2.init()
            captured = capsys.readouterr()
            assert_cmake_project_used_reinit_using_captured(cmake_project2, captured,
                                                          cmake_generator="ninja")
            # assert "CMAKE-INIT:  build (NEEDS-REINIT)" in captured.out
            # assert "CMAKE-INIT:  build (using cmake.generator=ninja)" in captured.out
            assert ctx.last_command == "cmake -G Ninja .."

    def test_build__auto_init_with_nonexisting_build_dir(self, tmpdir, capsys):
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="ninja")
        cmake_project1 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
        assert not project_build_dir.isdir()

        # -- STEP: First cmake_project.build => AUTO CMAKE-INIT: project_build_dir
        with cd(project_dir):
            assert not project_build_dir.exists()
            cmake_project1.build()

            # -- POSTCONDITIONS:
            expected_commands = [
                "cmake -G Ninja ..",
                "cmake --build .",
            ]
            assert ctx.commands == expected_commands
            cmake_build_filename = project_build_dir/CMakeProjectPersistentData.FILE_BASENAME
            captured = capsys.readouterr()
            assert_cmake_project_used_init_using_captured(cmake_project1, captured,
                                                          cmake_generator="ninja")
            # assert "CMAKE-INIT:  build (using cmake.generator=ninja)" in captured.out
            assert "CMAKE-BUILD: build" in captured.out
            assert project_build_dir.exists()
            assert cmake_build_filename.exists()


    def test_build__skip_init_with_existing_build_dir_and_same_data(self, tmpdir, capsys):
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="ninja")
        assert not project_build_dir.isdir()

        # -- STEP 1: First cmake_project.init
        with cd(project_dir):
            cmake_project1 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
            cmake_project1.init()

            # -- POSTCONDITIONS:
            cmake_build_filename = project_build_dir/CMakeProjectPersistentData.FILE_BASENAME
            assert project_build_dir.exists(), "ENSURE: project_build_dir exists"
            assert cmake_build_filename.exists()
            captured = capsys.readouterr()
            assert_cmake_project_used_init_using_captured(cmake_project1, captured,
                                                          cmake_generator="ninja")
            # assert "CMAKE-INIT:  build (using cmake.generator=ninja)" in captured.out
            assert ctx.last_command == "cmake -G Ninja .."

        # -- STEP 2: Second cmake_project.build => SKIP-INIT.
        ctx.clear()
        with cd(project_dir):
            cmake_project2 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
            assert not cmake_project2.needs_reinit()
            cmake_project2.build()

            # -- POSTCONDITIONS:
            expected_commands = ["cmake --build ."]
            assert ctx.commands == expected_commands
            captured = capsys.readouterr()
            assert_cmake_project_skipped_reinit_using_captured(cmake_project1, captured,
                                                               cmake_generator="ninja")
            assert "CMAKE-BUILD: build" in captured.out
            # assert "CMAKE-INIT:  build (SKIPPED: Initialized" in captured.out
            # -- NOT-CONTAINED IN CAPTURED OUTPUT:
            # assert "CMAKE-INIT: build (NEEDS-REINIT)" not in captured.out
            # assert "CMAKE-INIT: build (using cmake.generator=ninja)" not in captured.out

    def test_build__performs_reinit_with_existing_build_dir_and_other_cmake_generator(self, tmpdir, capsys):
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="ninja")
        assert not project_build_dir.isdir()

        # -- STEP 1: First cmake_project.init
        with cd(project_dir):
            cmake_project1 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
            cmake_project1.init()

            # -- POSTCONDITIONS:
            cmake_build_filename = project_build_dir/CMakeProjectPersistentData.FILE_BASENAME
            assert project_build_dir.exists(), "ENSURE: project_build_dir exists"
            assert cmake_build_filename.exists()
            captured = capsys.readouterr()
            assert_cmake_project_used_init_using_captured(cmake_project1, captured,
                                                          cmake_generator="ninja")
            # assert "CMAKE-INIT:  build (using cmake.generator=ninja)" in captured.out
            assert ctx.last_command == "cmake -G Ninja .."

        # -- STEP 2: Second cmake_project.build => REINIT.
        ctx.clear()
        with cd(project_dir):
            build_config.cmake_generator = "OTHER"   # ONLY-DEFAULT
            cmake_project2 = CMakeProject(ctx, project_dir, project_build_dir, build_config,
                                          cmake_generator="make")
            assert cmake_project2.needs_reinit()
            cmake_project2.build()

            # -- POSTCONDITIONS:
            expected_commands = [
                'cmake -G "Unix Makefiles" ..',
                "cmake --build ."
            ]
            assert ctx.commands == expected_commands
            captured = capsys.readouterr()
            assert_cmake_project_used_reinit_using_captured(cmake_project2, captured,
                                                            cmake_generator="make")
            # assert "CMAKE-INIT:  build (NEEDS-REINIT)" in captured.out
            # assert "CMAKE-INIT:  build (using cmake.generator=make)" in captured.out
            # assert "CMAKE-BUILD: build" in captured.out
            # -- NOT-CONTAINED IN CAPTURED OUTPUT:
            # assert "CMAKE-INIT:  build (SKIPPED: " not in captured.out

    def test_init__skips_reinit_with_existing_build_dir_and_generator_none(self, tmpdir, capsys):
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="ninja")
        assert not project_build_dir.isdir()

        # -- STEP 1: First cmake_project.init
        with cd(project_dir):
            cmake_project1 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
            cmake_project1.init()

            # -- POSTCONDITIONS:
            cmake_build_filename = project_build_dir/CMakeProjectPersistentData.FILE_BASENAME
            assert project_build_dir.exists(), "ENSURE: project_build_dir exists"
            assert cmake_build_filename.exists()
            captured = capsys.readouterr()
            assert_cmake_project_used_init_using_captured(cmake_project1, captured,
                                                          cmake_generator="ninja")
            # assert "CMAKE-INIT:  build (using cmake.generator=ninja)" in captured.out
            assert ctx.last_command == "cmake -G Ninja .."

        # -- STEP 2: Second cmake_project.build => SKIP-REINIT.
        # REASON:
        #   * Inherit stored.cmake_generator (if it is not overridden).
        #   * Keep stored.cmake_generator until explicit reinit.
        ctx.clear()
        with cd(project_dir):
            build_config.cmake_generator = "OTHER"  # -- ONLY DEFAULT-VALUE
            cmake_project2 = CMakeProject(ctx, project_dir, project_build_dir, build_config,
                                          cmake_generator=None)
            assert not cmake_project2.needs_reinit()
            cmake_project2.init()

            # -- POSTCONDITIONS:
            expected_commands = []
            assert ctx.commands == expected_commands
            captured = capsys.readouterr()
            assert_cmake_project_skipped_reinit_using_captured(cmake_project2, captured,
                                                               cmake_generator="ninja")
            # assert "CMAKE-INIT:  build (SKIPPED: Initialized with cmake.generator=" in captured.out
            # -- NOT-CONTAINED IN CAPTURED OUTPUT:
            # assert "CMAKE-INIT:  build (NEEDS-REINIT)" not in captured.out
            # assert "CMAKE-INIT:  build (using cmake.generator=make)" not in captured.out

    def test_init__when_build_dir_exists_with_other_persistent_schema(self, tmpdir, capsys):
        ctx = MockContext()
        project_dir = Path(str(tmpdir))
        project_build_dir = project_dir/"build"
        build_config = BuildConfig(cmake_generator="ninja", cmake_build_type="debug")
        assert not project_build_dir.isdir()

        # -- STEP 1: First cmake_project.init
        with cd(project_dir):
            cmake_project1 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
            cmake_project1.init()
            cmake_build_filename = project_build_dir / CMakeProjectPersistentData.FILE_BASENAME
            assert project_build_dir.exists(), "ENSURE: project_build_dir exists"
            assert cmake_build_filename.exists()

            # -- STEP: Fake cmake-build init with other persistent data schema.
            # HINT: May occur when cmake-build is updated, but project_build_dir still exists.
            with open(cmake_build_filename, "w") as f:
                f.write("""{ "other": 123, "cmake_generator": "ninja" }""")

        # -- STEP 2: Second try to cmake_project.init()
        # ENSURE: No failure / AssertionError occurs
        with cd(project_dir):
            cmake_project2 = CMakeProject(ctx, project_dir, project_build_dir, build_config)
            assert cmake_project2.initialized
            assert not cmake_project2.needs_reinit()
            assert cmake_project2.needs_update()
            cmake_project2.init()

            assert not cmake_project2.needs_reinit()
            assert not cmake_project2.needs_update()
            captured = capsys.readouterr()
            assert_cmake_project_used_update_using_captured(cmake_project2, captured,
                                                            cmake_generator="ninja")
