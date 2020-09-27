# -*- coding: UTF-8 -*-

from __future__ import absolute_import, print_function
from collections import OrderedDict
from cmake_build.model import CMakeProject
from cmake_build.config import CMakeProjectPersistConfig, BuildConfig
from path import Path
from invoke.util import cd

# ---------------------------------------------------------------------------
# CONSTANTS:
# ---------------------------------------------------------------------------
# CMAKE_PROJECT_BUILD_CONFIG_FILENAME = ".cmake_build.build_config.json"
# CMAKE_PROJECT_BUILD_CONFIG_FILENAME = CMakeProjectPersistConfig.FILE_BASENAME



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


def assert_cmake_project_needed_update_using_captured(cmake_project, captured, cmake_generator=""):
    build_dir = cmake_project.project_dir.relpathto(cmake_project.project_build_dir)
    assert "CMAKE-INIT:  {0} (NEEDS-UPDATE, using cmake.generator=".format(build_dir) in captured.out
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
            cmake_build_filename = project_build_dir / CMakeProjectPersistConfig.FILE_BASENAME
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
            cmake_build_filename = project_build_dir / CMakeProjectPersistConfig.FILE_BASENAME
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
            cmake_build_filename = project_build_dir / CMakeProjectPersistConfig.FILE_BASENAME
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
            cmake_build_filename = project_build_dir / CMakeProjectPersistConfig.FILE_BASENAME
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
            cmake_build_filename = project_build_dir / CMakeProjectPersistConfig.FILE_BASENAME
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
            cmake_build_filename = project_build_dir / CMakeProjectPersistConfig.FILE_BASENAME
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
            cmake_build_filename = project_build_dir / CMakeProjectPersistConfig.FILE_BASENAME
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
            assert_cmake_project_needed_update_using_captured(cmake_project2, captured,
                                                            cmake_generator="ninja")
