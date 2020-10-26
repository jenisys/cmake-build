# -*- coding: UTF-8 -*-
# pylint: disable=wrong-import-position, wrong-import-order
# pylint: disable=unused-argument, redefined-builtin
# pylint: disable=redefined-outer-name  # RELATED-TO: config
# pylint: disable=super-with-arguments, useless-object-inheritance  # RELATED-TO: Python3
"""
Invoke tasks for building C/C++ projects w/ CMake.

.. code-block:: YAML

    # -- FILE: invoke.yaml
    cmake:
        generator: ninja
        project_dirs:
          - 01_Program_example1
          - 01_Program_example2
          - CTEST_example1

.. seealso::

    * https://cmake.org
"""

from __future__ import absolute_import, print_function
from collections import OrderedDict
from pprint import pprint
from path import Path


# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
# from invoke.exceptions import Failure
from invoke import task, Collection, Context, Task
from invoke.exceptions import Exit

# -- TASK-LIBRARY:
from .tasklet.cleanup import cleanup_tasks, config_add_cleanup_dirs
from .model_builder import (
    make_cmake_projects, make_build_configs_map, BUILD_CONFIG_DEFAULT
)
from .model import CMakeBuildRunner
from .cmake_util import CPACK_GENERATOR


# -----------------------------------------------------------------------------
# TASK UTILITIES:
# -----------------------------------------------------------------------------
# CHECK-IF-REALLY-NEEDED:
# class CMakeBuildConfigNormalizer(object):
#
#     @staticmethod
#     def normalize_build_configs(config):
#         build_configs = config.build_configs
#         if isinstance(build_configs, (list, tuple)):
#             # -- CASE: Convert build_configs as list into dict.
#             the_build_configs = {}
#             for build_config in build_configs:
#                 the_build_configs[build_config] = {}
#             config.build_configs = the_build_configs
#
#     @classmethod
#     def normalize(cls, config):
#         # DISABLED: cls.normalize_build_configs(config)
#         pass


# -----------------------------------------------------------------------------
# SHARED-DATA FOR TASKS:
# -----------------------------------------------------------------------------
class CMakeBuildTaskSettings(object):
    """Shared inter-task configuration for CMake build task(s).

    .. code-block:: sh

        # -- NOTE: Test task should "inherit" the config value of the build task
        $ cmake-build build --build-config=Release test
        $ cmake-build build --config=Release test
    """
    REMEMBER_NAMES = ["build_config", "config"]

    def __init__(self, **kwargs):
        self.build_config = None
        self.config = None
        self._initialized = False
        for name, value in kwargs.items():
            setattr(self, name, value)

    def clear(self):
        self.build_config = None
        self.config = None
        self._initialized = False

    @property
    def initialized(self):
        return self._initialized

    def init_with_context_config(self, ctx_config):
        if not self.initialized:
            self.build_config = getattr(ctx_config, "build_config", None)
            self._initialized = True

    def remember_value(self, name, value):
        """Remember a setting and/or use a remembered value if value is None.
        A not-None value is afterwards remembered (internally stored her).

        :return: :param:`value` if value was not-none.
        :return: Remembered value if :param:`value` was None.
        """
        remembered_value = getattr(self, name, None)
        value = value or remembered_value
        if value:
            # -- REMEMBER-VALUE: For next cmake-build task
            setattr(self, name, value)
        return value

    def remember_data(self, data):
        """Implements the REMEMBER protocol:

        * If current value(s) is UNSPECIFIED, use REMEMBERED one
        * Store current SPECIFIED value(s) for later

        :param data:    Data dictionary with param name/value(s) (INOUT).
        :return: data (potentially modified)
        """
        for name in self.REMEMBER_NAMES:
            if name in data:
                value = data[name]
                data[name] = self.remember_value(name, value)
        return data

    def needs_remember(self, data):
        for name in self.REMEMBER_NAMES:
            if name in data:
                return True
        return False

    def remember_build_config(self, value):
        return self.remember_value("build_config", value)

    def remember_config(self, value):
        return self.remember_value("config", value)


# --------------------------------------------------------------------------------
# CLASS: CMakeBuildTask
# --------------------------------------------------------------------------------
class CMakeBuildTask(Task):
    """Special task class for CMakeBuild tasks to have more control:

    * override option names in a task
    * remember inter-task param values

    EXAMPLE: Override option names

    .. code-block:: py

        COMMON_OPTION_NAMES = {
            # -- CONSTRAINT: Requires that first name is the param-name.
            "define": ("define", "D"),
        }
        @task(klass=CMakeBuildTask, option_names=COMMON_OPTION_NAMES)
        def my_task(ctx, define=None, ...):
            ... # Whatever

    EXAMPLE: Remember inter-task settings (from preceeding tasks)

    .. code-block:: sh

        # -- SOME TASK PARAMS: Are remembered in next task(s)
        # APPLIES TO: config, build_config
        $ cmake-build build --config=Release test

        # -- NOTES:
        #   The "test" task has config=Release, remembered from "build" task.
    """
    task_settings = CMakeBuildTaskSettings()
    use_diag = False

    def __init__(self, body, name=None, **kwargs):
        option_names = kwargs.pop("option_names", None)
        super(CMakeBuildTask, self).__init__(body, name=name, **kwargs)
        self.overriden_option_names = option_names or dict()
        if self.use_diag:
            print("DIAG CMakeBuildTask.ctor: {0}".format(self.name))

    # -- SPECIAL TASK CLASS DETAILS:
    @staticmethod
    def cleanup_taken_names(taken_names, new_names, old_names=None):
        assert isinstance(taken_names, set)
        old_names = old_names or []
        taken_names = taken_names.symmetric_difference(old_names)
        taken_names.update(new_names)

    def override_option_names(self, name, data, taken_names):
        special_option_names = self.overriden_option_names.get(name)
        if special_option_names:
            initial_names = data["names"]
            data["names"] = special_option_names
            self.cleanup_taken_names(taken_names,
                                     special_option_names,
                                     initial_names)
        if self.use_diag:
            # pylint: disable=line-too-long
            print("DIAG CMakeBuildTask.arg_opts: name={0} names={1} (iterable: {2})".format(
                  name, data["names"], (name in self.iterable)))

    def remember_settings(self, data):
        """Remember inter-task settings (if they are not provided)"""
        self.task_settings.remember_data(data)

    @classmethod
    def clear_task_settings(cls):
        cls.task_settings.clear()

    # -- TASK CLASS RELATED:
    def arg_opts(self, name, default, taken_names):
        """Support to override the option.names of a task param."""
        data = super(CMakeBuildTask, self).arg_opts(name, default, taken_names)
        self.override_option_names(name, data, taken_names)
        return data

    def __call__(self, *args, **kwargs):
        if not isinstance(args[0], Context):
            # -- GUARD: Against calling tasks with no context.
            ctx = args[0]
            message = "Task expected a Context as first arg, got {} instead!"
            raise TypeError(message.format(type(ctx)))

        if self.task_settings.needs_remember(kwargs):
            ctx = args[0]
            self.task_settings.init_with_context_config(ctx.config)
            self.remember_settings(kwargs)
        return super(CMakeBuildTask, self).__call__(*args, **kwargs)


# -----------------------------------------------------------------------------
# TASKS SETTINGS:
# -----------------------------------------------------------------------------
# pylint: disable=line-too-long
TASK_HELP4PARAM_PROJECT = "CMake project directory (as path)"
TASK_HELP4PARAM_BUILD_CONFIG = "CMAKE_BUILD_CONFIG: debug, release, ... (as string)"
TASK_HELP4PARAM_CMAKE_CONFIG = "For CMake multi-config generators, like: Debug, Release, ..."
TASK_HELP4PARAM_CMAKE_GENERATOR = "CMAKE_GENERATOR: ninja, make, ... (as string)"
TASK_HELP4PARAM_CMAKE_DEFINE = "CMake define, like: -D NAME=VALUE (many)"
TASK_HELP4PARAM_CMAKE_INIT_ARG = "CMake init arg to use (many)"
TASK_HELP4PARAM_CMAKE_BUILD_ARG = "CMake build arg to use (many)"
TASK_HELP4PARAM_CMAKE_BUILD_OPTION = "CMake build option to use (many)"
TASK_HELP4PARAM_CMAKE_OPTION = "CMake option to use (many)"
TASK_HELP4PARAM_CTEST_ARG = "CMake test arg (many)"

SPECIAL_OPTION_NAMES = {
    # MAYBE: "config": ("config", "c"),
    "define": ("define", "D"),
}


# pylint: enable=line-too-long
# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
@task(iterable=["define", "arg"],
      klass=CMakeBuildTask, option_names=SPECIAL_OPTION_NAMES,
      help={
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
        "arg": TASK_HELP4PARAM_CMAKE_INIT_ARG,
        "define": TASK_HELP4PARAM_CMAKE_DEFINE,
        "clean-config": "Remove stored_config before init (optional)",
})
def init(ctx, project="all", build_config=None, generator=None,
         define=None, config=None, clean_config=False, arg=None):
    """Initialize cmake project(s) (generate: build-scripts).

    POSTCONDITION:
     * cmake_project build_dir exists (is created if necessary)
     * cmake_project build-scripts are generated/updated with existing config.
    """
    cmake_defines = define or []
    cmake_init_args = arg or []

    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        if clean_config:
            # -- ENSURE:
            # Use clean cmake_project.config based on build_config data.
            cmake_project.remove_stored_config()
            cmake_project.reset_config()

        if cmake_defines:
            cmake_project.config.add_cmake_defines(cmake_defines)
        cmake_project.init(args=cmake_init_args, config=config)


@task(iterable=["arg", "option", "init_arg", "define"],
      klass=CMakeBuildTask, option_names=SPECIAL_OPTION_NAMES,
      help={
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "arg": TASK_HELP4PARAM_CMAKE_BUILD_ARG,
        "option": TASK_HELP4PARAM_CMAKE_BUILD_OPTION,
        "init-arg": TASK_HELP4PARAM_CMAKE_INIT_ARG,
        "define": TASK_HELP4PARAM_CMAKE_DEFINE,
        "target": "CMake build target to use (optional)",
        "jobs": "CMAKE_PARALLEL value (as int)",
        "clean-first": "Use clean-first before build (optional)",
        "verbose": "Use CMake build verbose mode (optional)",
})
def build(ctx, project="all", build_config=None, generator=None, config=None,
          arg=None, option=None, init_arg=None, define=None,
          target=None, jobs=-1, clean_first=False, verbose=False):
    # pylint: disable=too-many-arguments, too-many-locals
    """Build cmake project(s)."""
    # -- HINT: Invoke default tasks needs default values for iterable params.
    cmake_build_args = arg or []
    cmake_build_options = option or []
    cmake_init_args = init_arg or []
    cmake_defines = define or []

    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        if cmake_defines:
            cmake_project.config.add_cmake_defines(cmake_defines)
        cmake_project.build(args=cmake_build_args,
                            options=cmake_build_options,
                            init_args=cmake_init_args,
                            config=config,
                            target=target,
                            parallel=jobs,
                            clean_first=clean_first,
                            verbose=verbose)


@task(aliases=["ctest"], iterable=["arg", "init_arg"],
      klass=CMakeBuildTask, # DISABLED: option_names=SPECIAL_OPTION_NAMES,
      help={
        "arg": TASK_HELP4PARAM_CTEST_ARG,
        "init-arg": TASK_HELP4PARAM_CMAKE_INIT_ARG,
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
        "verbose": "Use verbose mode (optional)",
        # -- CTEST SPECIFIC OPTIONS:
        "repeat": "Repeat tests (until-pass:n, until-fail:n, after-timeout:n).",
        "rerun-failed": "Rerun failed tests.",
        "output-log": "Use --output-log=<FILE>",
        "output-on-failure": "Show test output when failure(s) occur.",
        "stop-on-failure":   "Stop test-run when failure(s) occur.",
        "progress": "Show progress.",
        "jobs": "Number of jobs (as int, CMAKE_PARALLEL).",
})
def test(ctx, project="all", build_config=None, config=None, generator=None,
         arg=None, init_arg=None, verbose=False,
         # -- CTEST SPECIFIC:
         repeat=None, rerun_failed=False, output_log=None,
         output_on_failure=False, stop_on_failure=False, jobs=0, progress=False):
    # pylint: disable=too-many-arguments, too-many-locals
    """Test cmake projects (performs: ctest)."""
    ctest_args = arg or []
    cmake_init_args = init_arg or []

    # -- CTEST OPTIONS:
    if repeat:
        ctest_args.append("--repeat {0}".format(repeat))
    if rerun_failed:
        ctest_args.append("--rerun-failed")
    if output_on_failure:
        # -- RELATED: CTEST_OUTPUT_ON_FAILURE (environment variable)
        ctest_args.append("--output-on-failure")
    if stop_on_failure:
        ctest_args.append("--stop-on-failure")
    if progress:
        ctest_args.append("--progress")
    if output_log:
        ctest_args.append("--output-log {0}".format(output_log))
    if jobs:
        ctest_args.append("--parallel {0}".format(jobs))

    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.test(args=ctest_args,
                           init_args=cmake_init_args,
                           config=config,
                           verbose=verbose)


@task(klass=CMakeBuildTask,  # DISABLED: option_names=SPECIAL_OPTION_NAMES,
    help={
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
        # -- INSTALL TASK SPECIFIC:
        "prefix": "CMAKE_INSTALL_PREFIX to use (or use preconfigured)",
        "use_sudo": "Use sudo for install command",
})
def install(ctx, project="all", build_config=None, config=None, generator=None,
            prefix=None, use_sudo=False):
    """Install the build artifacts of cmake project(s)."""
    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.install(prefix=prefix, use_sudo=use_sudo, config=config)


@task(klass=CMakeBuildTask,  # DISABLED: option_names=SPECIAL_OPTION_NAMES,
    help={
        "project":      TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config":       TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator":    TASK_HELP4PARAM_CMAKE_GENERATOR,
        # -- TASK SPECIFIC PARAMS:
        "format":       "cpack.generator to use: TGZ, ZIP, ... (CPACK_GENERATOR)",
        "package-dir":  "Override: CPACK_PACKAGE_DIRECTORY (optional)",
        "cpack-config": "CPack config-file to use (default: CPackConfig.cmake)",
        "source-bundle": "Create a source bundle (instead of: binary package)",
        "source":       "Create a source bundle (same as: --source-bundle)",
        "vendor":       "Override: CPACK_PACKAGE_VENDOR (optional)",
        "verbose":      "Run cpack in verbose mode (optional)",
        # -- OPTIONAL: Check if needed.
        "target": "CMake build target before cpack is used (optional)",
})
def pack(ctx, format=None,
         project="all", build_config=None, config=None, generator=None,
         target=None,
         package_dir=None, cpack_config=None,
         source=False, source_bundle=False, vendor=None, verbose=False):
    # pylint: disable=too-many-arguments
    """Pack a source-code archive or a binary bundle/archive for cmake project(s)."""
    # TODO: config => cmake_project.build(...), cmake_project.pack(...)

    # MAYBE: cpack_defines
    source_bundle = source_bundle or source
    if not format:
        format = CPACK_GENERATOR

    cmake_projects = make_cmake_projects(ctx, project, build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        if target:
            cmake_project.build(target=target)
        cmake_project.pack(format=format, package_dir=package_dir,
                           cpack_config=cpack_config,
                           source_bundle=source_bundle,
                           vendor=vendor, verbose=verbose)
        print()


@task(aliases=["update"], iterable=["define"],
      klass=CMakeBuildTask, option_names=SPECIAL_OPTION_NAMES,
      help={
        "define": TASK_HELP4PARAM_CMAKE_DEFINE,
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
})
def configure(ctx, define, project="all", build_config=None, config=None,
                  generator=None):
    """Configure the CMake build_dir for cmake project(s)."""
    # XXX_TODO: config
    cmake_define_parts = define or []  # List of cmake definitions: NAME=VALUE
    cmake_defines_data = OrderedDict()
    bad_defines = []
    for name_value in cmake_define_parts:
        if "=" not in name_value or name_value.endswith("="):
            print("INVALID-DEFINE: %s (use schema: name=value)" % name_value)
            bad_defines.append(name_value)
            continue

        parts = name_value.split("=", 1)
        name, value = parts
        cmake_defines_data[name] = value

    if bad_defines:
        raise Exit("BAD-DEFINES: %s" % ", ".join(bad_defines))

    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator)
    for cmake_project in cmake_projects:
        cmake_project.configure(**cmake_defines_data)


@task(iterable=["arg", "option"],
      klass=CMakeBuildTask, option_names=SPECIAL_OPTION_NAMES,
      help={
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "arg": "CMake build clean argument (many)",
        "option": TASK_HELP4PARAM_CMAKE_OPTION,
})
def clean(ctx, project="all", build_config=None, config=None,
          arg=None, option=None, dry_run=False, strict=True):
    """Clean cmake project(s) by using the build system."""
    cmake_args = arg or []
    cmake_options = option or []

    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         strict=True)   # MAYBE: strict=strict
    for cmake_project in cmake_projects:
        cmake_project.clean(args=cmake_args, options=cmake_options, config=config)
        # LATER: config=config)
        # MAYBE: dry_run=dry_run)


@task(iterable=["arg", "option"], klass=CMakeBuildTask)
def clean_and_ignore_failures(ctx, project="all", build_config=None, config=None,
                              arg=None, option=None, dry_run=False):
    """Perform build-system clean target and ignore any failures (best-effort)."""
    cmake_args = arg or []
    cmake_options = option or []
    clean(ctx, project=project, build_config=build_config, config=config,
          arg=cmake_args, option=cmake_options, strict=False)


@task(iterable=["arg", "define"],
      klass=CMakeBuildTask, option_names=SPECIAL_OPTION_NAMES,
      help={
        "arg": TASK_HELP4PARAM_CMAKE_INIT_ARG,
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
})
def reinit(ctx, project="all", build_config=None, config=None, generator=None,
           arg=None, define=None):
    """Reinit cmake projects (performs: cleanup, init)."""
    # -- HINT: Preserve pre-existing cmake_project.cmake_generator
    cmake_init_args = arg or []
    cmake_defines = define or []    # TODO
    if cmake_defines:
        print("IGNORE: cmake_defines: {0}".format(cmake_defines))

    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         init_args=cmake_init_args)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.reinit(args=cmake_init_args, config=config)
    # PREPARED, TODO: dry_run=dry_run)


@task(iterable=["arg", "init_arg", "option"],
      klass=CMakeBuildTask,
      help={
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
        "arg": TASK_HELP4PARAM_CMAKE_BUILD_ARG,
        "init-arg": TASK_HELP4PARAM_CMAKE_INIT_ARG,
        "option": TASK_HELP4PARAM_CMAKE_BUILD_OPTION,
})
def rebuild(ctx, project="all", build_config=None, config=None, generator=None,
            arg=None, init_arg=None, option=None):
    """Rebuild cmake projects (performs: clean, build)."""
    cmake_build_args = arg or []
    cmake_init_args = init_arg or []
    cmake_options = option or []

    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config)
    cmake_runner = CMakeBuildRunner(cmake_projects)
    if generator:
        # -- OVERRIDE: cmake_generator for all cmake_projects
        cmake_runner.set_cmake_generator(generator)
    cmake_runner.rebuild(args=cmake_build_args, options=cmake_options,
                         init_args=cmake_init_args, config=config)
    # PREPARED, TODO: dry_run=dry_run)


@task(iterable=["arg", "init_arg", "test_arg"],
      klass=CMakeBuildTask,
      help={
        "project": TASK_HELP4PARAM_PROJECT,
        "build-config": TASK_HELP4PARAM_BUILD_CONFIG,
        "config": TASK_HELP4PARAM_CMAKE_CONFIG,
        "generator": TASK_HELP4PARAM_CMAKE_GENERATOR,
        "arg": TASK_HELP4PARAM_CMAKE_BUILD_ARG,
        "init-arg": TASK_HELP4PARAM_CMAKE_INIT_ARG,
        "test-arg": TASK_HELP4PARAM_CTEST_ARG,
        "use-test": "Perform CMake test step (optional)",
})
def redo(ctx, project="all", build_config=None, config=None, generator=None,
         arg=None, init_arg=None, test_arg=None, use_test=False):
    """Build cycle for cmake project(s) (performs: reinit, build, ...).

    Steps:

    - cmake.reinit
    - cmake.build
    - OPTIONAL: cmake.test (= ctest)  -- enabled via: --use-test option
    """
    cmake_build_args = arg or []
    cmake_init_args = init_arg or []
    cmake_options = []
    ctest_args = test_arg or []

    cmake_projects = make_cmake_projects(ctx, project,
                                         build_config=build_config,
                                         generator=generator,
                                         init_args=cmake_init_args)
    for cmake_project in cmake_projects:
        cmake_project.reinit(args=cmake_init_args, config=config)
        cmake_project.build(args=cmake_build_args, config=config)
                            # MAYBE: options=cmake_options)
        if use_test:
            cmake_project.test(args=ctest_args, config=config)


def cmake_build_show_projects(projects):
    print("PROJECTS[%d]:" % len(projects))
    for project in projects:
        project = Path(project)
        annotation = ""
        if not project.isdir():
            annotation = "NOT-EXISTS"
        print("  - {project} {note}".format(project=project, note=annotation))


def cmake_build_show_build_configs(build_configs):
    print("BUILD_CONFIGS[%d]:" % len(build_configs))
    for build_config in build_configs:
        print("  - {build_config}".format(build_config=build_config))


@task
def config(ctx):
    """Show cmake-build configuration details."""
    # config = ctx.config
    if not ctx.config.build_configs_map:
        build_configs_map = make_build_configs_map(ctx.config.build_configs)
        ctx.config.build_configs_map = build_configs_map

    print("cmake_generator: %s" % ctx.config.cmake_generator)
    cmake_build_show_build_configs(ctx.config.build_configs)
    cmake_build_show_projects(ctx.config.projects)
    pprint(ctx.config, indent=4)
    print("-------------------------")
    pprint(dict(ctx.config), indent=4)


# -----------------------------------------------------------------------------
# TASK CONFIGURATION:
# -----------------------------------------------------------------------------
namespace = Collection(redo, init, test, clean, reinit, rebuild, config)
namespace.add_task(build, default=True)
namespace.add_task(install)
namespace.add_task(pack)
namespace.add_task(configure)


# pylint: disable=line-too-long
TASKS_CONFIG_DEFAULTS = {
    "cmake_generator": None,
    "cmake_toolchain": None,
    "cmake_install_prefix": None,
    "cmake_defines": None,
    "build_dir_schema": "build.{BUILD_CONFIG}",
    "build_config": BUILD_CONFIG_DEFAULT,
    "build_configs": [],
    "build_config_aliases": {}, # HINT: Map string -> sequence<string> (or string/callable)
    "build_configs_map": {},    # -- AVOID-HERE: BUILD_CONFIG_DEFAULT_MAP.copy(),
    "projects": [],
    "config_file": None,
    "config_dir": None,
}
# pylint: enable=line-too-long
namespace.configure(TASKS_CONFIG_DEFAULTS)
namespace.configuration({})

# -- REGISTER CLEANUP TASKS:
cleanup_tasks.add_task(clean_and_ignore_failures, "clean_cmake-build")
cleanup_tasks.configure(namespace.configuration({}))

# -- REGISTER DEFAULT CLEANUP_DIRS (if configfile is not provided):
# HINT: build_dir_schema: build.{BUILD_CONFIG}
config_add_cleanup_dirs(["build.*"])
