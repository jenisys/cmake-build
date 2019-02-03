# -*- coding: UTF-8 -*-
"""
Contains the CMake model entities to simplify interaction with `CMake`_.

.. _CMake: https://cmake.org/
"""

from __future__ import absolute_import, print_function

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
from .cmake_util import \
    make_build_dir_from_schema, map_build_config_to_cmake_build_type, \
    cmake_cmdline, cmake_cmdline_generator_option, \
    cmake_defines_add    as _cmake_defines_add, \
    cmake_defines_remove as _cmake_defines_remove
from .persist import PersistentData, Unknown
from invoke.util import cd
from path import Path


# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
CMAKE_CONFIG_DEFAULTS = {
    "cmake_generator": None,
    "cmake_toolchain": None,
    "cmake_build_type": None,
    "cmake_defines": [],
    "cmake_args": [],
}


# -----------------------------------------------------------------------------
# CMAKE UTILITY CLASSES:
# -----------------------------------------------------------------------------
class CMakeProjectData(object):

    def __init__(self, data=None, use_defaults=True, **kwargs):
        data_defaults = {}
        if use_defaults:
            data_defaults = CMAKE_CONFIG_DEFAULTS.copy()
        self.data = data_defaults
        self.data.update(data or {})
        self.data.update(kwargs)

    def clear(self):
        self.data.clear()

    def get(self, name, default=None):
        return self.data.get(name, default)
        # value = getattr(self, name, Unknown)
        # if value is Unknown:
        #     value = self.data.get(name, default)
        # return value

    def update(self, data, **kwargs):
        self.data.update(data, **kwargs)

    def copy(self):
        return self.__class__(data=self.data.copy())

    def assign(self, data):
        # -- WORKS WITH: this-class or dict-like
        the_data = data
        if isinstance(data, self.__class__):
            the_data = data.data
        self.data = the_data.copy()

    def __len__(self):
        return len(self.data)

    def __contains__(self, param_name):
        return param_name in self.data

    def __getitem__(self, param_name):
        return self.data[param_name]

    def __setitem__(self, param_name, value):
        self.data[param_name] = value

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.data == other
        else:
            return self.data == other.data

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def cmake_generator(self):
        return self.get("cmake_generator", None)

    @cmake_generator.setter
    def cmake_generator(self, value):
        self.data["cmake_generator"] = value

    @property
    def cmake_toolchain(self):
        return self.get("cmake_toolchain", None)

    @cmake_toolchain.setter
    def cmake_toolchain(self, value):
        self.data["cmake_toolchain"] = value

    @property
    def cmake_build_type(self):
        return self.get("cmake_build_type", None)

    @cmake_build_type.setter
    def cmake_build_type(self, value):
        self.data["cmake_build_type"] = value

    @property
    def cmake_defines(self):
        return self.get("cmake_defines", [])

    @cmake_defines.setter
    def cmake_defines(self, value):
        self.data["cmake_defines"] = value or []

    @property
    def cmake_args(self):
        return self.get("cmake_args", [])

    @cmake_args.setter
    def cmake_args(self, value):
        self.data["cmake_args"] = value or []

    def cmake_defines_add(self, name, value=None):
        cmake_defines = self.cmake_defines
        _cmake_defines_add(cmake_defines, name, value)
        # self.cmake_defines = cmake_defines

    def cmake_defines_remove(self, name):
        cmake_defines = self.cmake_defines
        _cmake_defines_remove(cmake_defines, name)
        # self.cmake_defines = cmake_defines


class CMakeProjectPersistentData(CMakeProjectData, PersistentData):
    """Persistent data class for CMake project (build_dir) data.
    This data represents one build-configuration of this project.
    """
    FILE_BASENAME = ".cmake_build.build_config.json"

    def __init__(self, filename=None, data=None, cmake_generator=None, cmake_toolchain=None, **kwargs):
        # -- OPTIONAL OVERRIDE:
        the_data = data or {}
        if cmake_generator:
            the_data["cmake_generator"] = cmake_generator
        if cmake_toolchain:
            the_data["cmake_toolchain"] = cmake_toolchain
        # -- SETUP/INIT: BASE-CLASSES
        CMakeProjectData.__init__(self, data=the_data, **kwargs)
        PersistentData.__init__(self, filename, data=self.data)


class BuildConfig(CMakeProjectData):
    """Represent the configuration data related to a build-configuration.


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
    DEFAULT_NAME = "default"
    CMAKE_BUILD_TYPE_AUTO_DETECT = True

    def __init__(self, name=None, data=None, **kwargs):
        CMakeProjectData.__init__(self, data, **kwargs)
        self.name = name or self.DEFAULT_NAME
        self._cmake_build_type = self.cmake_build_type
        self.derive_cmake_build_type_if_unconfigured()

    def derive_cmake_build_type(self):
        """Derives CMAKE_BUILD_TYPE from build_config.name."""
        return map_build_config_to_cmake_build_type(self.name)

    def derive_cmake_build_type_and_assign(self, force=False):
        """Derives CMAKE_BUILD_TYPE and assigns it,
        if the CMAKE_BUILD_TYPE is not configured yet.
        """
        if force or self.CMAKE_BUILD_TYPE_AUTO_DETECT:
            # -- NOT-CONFIGURED: cmake_build_type
            # HINT: Derive cmake_build_type from build_config.name
            self.cmake_build_type = self.derive_cmake_build_type()
        return self.cmake_build_type

    def derive_cmake_build_type_if_unconfigured(self):
        """Derives CMAKE_BUILD_TYPE and assigns it,
        if the CMAKE_BUILD_TYPE is not configured yet.
        """
        not_configured = not self._cmake_build_type
        if not_configured:
            self.derive_cmake_build_type_and_assign()
        return self.cmake_build_type

    @property
    def cmake_build_type(self):
        return self.data["cmake_build_type"]

    @cmake_build_type.setter
    def cmake_build_type(self, value):
        self.data["cmake_build_type"] = value
        self._cmake_build_type = value


class CMakeProject(object):
    """CMake project entity that represents a
    CMake project with one build configuration (one build_dir).

    RESPONSIBILITIES:
    * Can initialize a CMake project (and its build_dir)
    * Can cleanup/remove the CMake project build_dir (and its build artifacts)
    * Stores cmake-init configuration data in the build_dir
    * Can detect when the cmake-init configuration data changes
      and automatically triggers a cmake-reinit of the build_dir
      (example: another toolchain is used, cmake-init definitions change, ...)
    """
    CMAKE_BUILD_DATA_FILENAME = ".cmake_build.build_config.json"
    CMAKE_BUILD_TYPE_DEFAULT = "Debug"
    REBUILD_USE_DEEP_CLEANUP = False

    def __init__(self, ctx, project_dir=None, project_build_dir=None,
                 build_config=None, cmake_generator=None):
        if build_config is None:
            cmake_build_type = self.CMAKE_BUILD_TYPE_DEFAULT
            build_config = BuildConfig("default", cmake_build_type=cmake_build_type)

        project_dir = Path(project_dir or ".")
        project_dir = project_dir.abspath()
        if not project_build_dir:
            build_dir = make_build_dir_from_schema(ctx.config, build_config.name)
            project_build_dir = project_dir/build_dir

        cmake_generator_default = build_config.cmake_generator
        cmake_toolchain = build_config.cmake_toolchain

        self.ctx = ctx
        self.project_dir = project_dir
        self.project_build_dir = Path(project_build_dir).abspath()
        self.build_config = build_config
        self.current_data = None
        self.stored_data = None
        self._dirty = True
        self.load_cmake_build_data()
        self.update_from_build_config()
        if not cmake_generator:
            # -- INHERIT: Stored cmake_generator, if it is not overridden.
            cmake_generator = self.stored_data.cmake_generator or cmake_generator_default
        self.cmake_generator = cmake_generator
        self.cmake_toolchain = cmake_toolchain
        self._dirty = True

    def reset_dirty(self):
        self._dirty = False

    def exists(self):
        return self.project_dir.isdir()

    @property
    def dirty(self):
        return self._dirty or (self.current_data != self.stored_data)
        # MAYBE: not self.stored_data.exists()

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    @property
    def cmake_build_data_filename(self):
        return self.project_build_dir/self.CMAKE_BUILD_DATA_FILENAME

    @property
    def cmake_toolchain(self):
        return self.current_data.cmake_toolchain

    @cmake_toolchain.setter
    def cmake_toolchain(self, value):
        self.current_data.cmake_toolchain = value
        self.dirty = True

    @property
    def cmake_generator(self):
        return self.current_data.cmake_generator

    @cmake_generator.setter
    def cmake_generator(self, value):
        self.current_data.cmake_generator = value
        self.dirty = True

    def _on_cmake_build_data_loaded(self, data):
        # XXX-JE-CHECK-REALLY-NEEDED
        pass

    def update_from_build_config(self):
        """Update attr:`current_data` from the :attr:`build_config` data."""
        self.current_data.cmake_toolchain = self.build_config.cmake_toolchain
        self.current_data.cmake_generator = self.build_config.cmake_generator
        self.current_data.cmake_build_type = self.build_config.cmake_build_type
        self.current_data.cmake_defines = self.build_config.cmake_defines
        self.current_data.cmake_args = self.build_config.cmake_args

    def load_cmake_build_data(self):
        cmake_build_data_filename = self.cmake_build_data_filename
        file_exists = cmake_build_data_filename.exists()
        data = CMakeProjectPersistentData.load(cmake_build_data_filename)
        self._on_cmake_build_data_loaded(data)
        self.stored_data = data
        self.current_data = data.copy()
        self.reset_dirty()
        if not file_exists:
            self.dirty = True

    # def load_cmake_build_data_and_merge(self):
    #     self.load_cmake_build_data()
    #     self.current_data.data["cmake_generator"] = self.cmake_generator
    #     self.current_data.data["cmake_toolchain"] = self.cmake_toolchain
    #     self.dirty = self.current_data != self.stored_data

    def store_cmake_build_data(self):
        cmake_build_data_filename = self.cmake_build_data_filename
        self.current_data["cmake_generator"] = self.cmake_generator
        store_always = False
        if (not cmake_build_data_filename.exists() or store_always or
           (self.current_data != self.stored_data)):
            # -- STORE DATA (persistently):
            self.current_data.save(self.cmake_build_data_filename)
            self.stored_data = self.current_data.copy()
        self.dirty = False

    # def make_cmake_generator_option(self, cmake_generator=None):
    #     cmake_generator = cmake_generator or self.cmake_generator
    #     return cmake_cmdline_generator_option(cmake_generator)
    #
    def make_cmake_init_options(self, cmake_generator=None):
        cmake_toolchain = self.current_data.cmake_toolchain
        cmake_generator = self.current_data.cmake_generator
        cmdline = cmake_cmdline(args=self.build_config.cmake_args,
                                defines=self.build_config.cmake_defines,
                                generator=cmake_generator,
                                toolchain=cmake_toolchain,
                                build_type=self.build_config.cmake_build_type)
        return cmdline

    def has_cmake_build_data_file(self):
        return self.cmake_build_data_filename.exists()

    @property
    def initialized(self):
        print("XXX cmake_project.initialized:")
        print("XXX   project_build_dir=%s (exists=%s)" % (self.project_build_dir, self.project_build_dir.exists()))
        print("XXX   cmake_build_data_file=%s (exists=%s)" % (self.cmake_build_data_filename, self.has_cmake_build_data_file()))
        print("XXX cmake_project.initialized:")
        return (self.project_build_dir.exists() and self.has_cmake_build_data_file())
                # XXX cmake_stored_generator
                # XXX and self.cmake_stored_generator == self.cmake_generator)

    def needs_reinit(self):
        return ((self.current_data != self.stored_data) or
                not self.cmake_build_data_filename.exists())
                # XXX or self.dirty)

    # -- PROJECT-COMMAND API:
    def cleanup(self):
        if self.project_build_dir.isdir():
            "CMAKE-CLEANUP: {0}".format(self.project_build_dir.relpath())
            self.project_build_dir.rmtree_p()

    def ensure_init(self, args=None, cmake_generator=None): # @simplify
        project_build_dir = self.project_build_dir.relpath()
        if self.initialized and not self.needs_reinit():
            # -- CASE: ALREADY DONE w/ same cmake_generator.
            print("CMAKE-INIT:  {0} (SKIPPED: Initialized with cmake.generator={1})."\
                  .format(project_build_dir, self.cmake_generator))
            return False

        if self.project_build_dir.isdir():
            print("CMAKE-INIT:  {0} (NEEDS-REINIT)".format(project_build_dir))
            self.cleanup()

        cmake_generator = cmake_generator or self.cmake_generator
        ctx = self.ctx
        self.project_build_dir.makedirs_p()
        with cd(self.project_build_dir):
            print("CMAKE-INIT:  {0} (using cmake.generator={1})".format(
                  project_build_dir, cmake_generator))

            cmake_init_options = self.make_cmake_init_options(cmake_generator)
            relpath_to_project_dir = self.project_build_dir.relpathto(self.project_dir)
            ctx.run("cmake {options} {relpath}".format(
                    options=cmake_init_options, relpath=relpath_to_project_dir))
            print()

            # -- FINALLY: If cmake-init worked, store used cmake_generator.
            self.cmake_generator = cmake_generator
            self.store_cmake_build_data()
        return True

    def init(self, args=None, cmake_generator=None):
        """Perform CMake init of the project build directory for this build_config."""
        return self.ensure_init(args=args, cmake_generator=cmake_generator)

    def build(self, args=None, init_args=None, cmake_generator=None, ensure_init=True):
        """Triggers the cmake.build step (and delegate to used build-system)."""
        cmake_build_args = ""
        if args:
            cmake_build_args = "-- {0}".format(args)

        project_build_dir = self.project_build_dir.relpath()
        if ensure_init:
            self.ensure_init(args=init_args, cmake_generator=cmake_generator)
        self.project_build_dir.makedirs_p()
        with cd(self.project_build_dir):
            print("CMAKE-BUILD: {0}".format(project_build_dir))
            self.ctx.run("cmake --build . {0}".format(cmake_build_args).strip())
            print()

    def clean(self, init_args=None):
        """Clean the build artifacts (but: preserve CMake init)"""
        project_build_dir = self.project_build_dir.relpath()
        if not self.initialized:
            print("CMAKE-CLEAN: {0} (SKIPPED: not initialized yet)".format(project_build_dir))
            return

        # -- ALTERNATIVE: self.build(args="clean", ensure_init=False)
        self.ensure_init(args=init_args)
        print("CMAKE-CLEAN: {0}".format(project_build_dir))
        cmake_build_args = "clean"
        with cd(self.project_build_dir):
            self.ctx.run("cmake --build . -- {0}".format(cmake_build_args))

    def reinit(self, args=None):
        self.cleanup()
        self.init(args=args)

    def rebuild(self, args=None, init_args=None):
        if self.REBUILD_USE_DEEP_CLEANUP:
            self.cleanup()

        self.clean(init_args=init_args)
        self.build(args=args, ensure_init=True)

    def ctest(self, args=None, init_args=None):
        ctest_args = ""
        if args:
            ctest_args = " ".join(args)

        project_build_dir = self.project_build_dir.relpath()
        self.ensure_init(args=init_args)
        self.project_build_dir.makedirs_p()
        with cd(self.project_build_dir):
            print("CMAKE-TEST:  {0}".format(project_build_dir))
            self.ctx.run("ctest {0}".format(ctest_args))
            print()

    def test(self, args=None, init_args=None):
        return self.ctest(args=args, init_args=init_args)


class CMakeBuildRunner(object):
    """Build runner for many CMake projects (composite)."""
    def __init__(self, cmake_projects=None, target=None):
        self.cmake_projects = cmake_projects or []
        self.default_target = target or "build"

    def execute_target(self, target):
        target = target or self.default_target
        for cmake_project in self.cmake_projects:
            project_target_func = getattr(cmake_project, target, None)
            if project_target_func:
                project_target_func()
            else:
                print("CMAKE-BUILD: Skip target={0} for {1} (not-supported)".format(
                    target, cmake_project
                ))

    def __call__(self, target=None):
        self.execute_target(target)

    def set_cmake_generator(self, cmake_generator=None):
        # -- OVERRIDE: cmake_generator
        for cmake_project in self.cmake_projects:
            cmake_project.cmake_generator = cmake_generator

    def run(self, target=None):
        self.execute_target(target)

    def init(self):
        self.execute_target("init")

    def build(self):
        self.execute_target("build")

    def test(self):
        self.execute_target("test")

    def reinit(self):
        self.execute_target("cleanup")
        self.execute_target("init")

    def rebuild(self):
        self.execute_target("rebuild")

    def clean(self):
        self.execute_target("cleanup")

    def cleanup(self):
        self.execute_target("cleanup")
