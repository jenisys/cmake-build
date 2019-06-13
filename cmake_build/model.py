# -*- coding: UTF-8 -*-
# pylint: disable=no-value-for-parameter, invalid-name
"""
Contains the CMake model entities to simplify interaction with `CMake`_.

.. _CMake: https://cmake.org/
"""

from __future__ import absolute_import, print_function

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
import os
import six
from collections import OrderedDict
from invoke.util import cd
from path import Path
from .cmake_util import \
    make_build_dir_from_schema, map_build_config_to_cmake_build_type, \
    cmake_cmdline, cmake_cmdline_define_options
from .exceptions import NiceFailure
from .persist import PersistentData
from .pathutil import posixpath_normpath


# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
CMAKE_CONFIG_DEFAULTS = {
    "cmake_generator": None,
    "cmake_toolchain": None,
    "cmake_build_type": None,
    "cmake_install_prefix": None,
    "cmake_defines": [],
    "cmake_args": [],
}
CMAKE_BUILD_VERBOSE = (os.environ.get("CMAKE_BUILD_VERBOSE", None) == "yes")


def make_args_string(args):
    """Build args-string from args as string or list."""
    if not args:
        return ""

    if not isinstance(args, six.string_types):
        assert isinstance(args, (list, tuple))
        args = " ".join([str(x) for x in args])
    args_text = "{0}".format(args)
    return args_text.strip()


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
        self.normalize_data()

    def normalize_data(self):
        cmake_defines = self.data.get("cmake_defines", None)
        if cmake_defines is None:
            cmake_defines = []
        if not isinstance(cmake_defines, OrderedDict):
            self.data["cmake_defines"] = OrderedDict(cmake_defines)

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
        self.normalize_data()

    def copy(self):
        return self.__class__(data=self.data.copy())

    def assign(self, data):
        # -- WORKS WITH: this-class or dict-like
        the_data = data
        if isinstance(data, self.__class__):
            the_data = data.data
        self.data = the_data.copy()
        self.normalize_data()

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
    def cmake_install_prefix(self):
        return self.get("cmake_install_prefix", None)

    @cmake_install_prefix.setter
    def cmake_install_prefix(self, value):
        self.data["cmake_install_prefix"] = value

    @property
    def cmake_defines(self):
        return self.data["cmake_defines"]

    @cmake_defines.setter
    def cmake_defines(self, value):
        if not isinstance(value, OrderedDict):
            value = OrderedDict(value)
        self.data["cmake_defines"] = value

    @property
    def cmake_args(self):
        return self.get("cmake_args", [])

    @cmake_args.setter
    def cmake_args(self, value):
        self.data["cmake_args"] = value or []

    def cmake_defines_add(self, name, value=None):
        self.cmake_defines.update([(name, value)])

    def cmake_defines_remove(self, name):
        if name in self.cmake_defines:
            self.cmake_defines.pop(name)


class CMakeProjectPersistentData(CMakeProjectData, PersistentData):
    """Persistent data class for CMake project (build_dir) data.
    This data represents one build-configuration of this project.
    """
    FILE_BASENAME = ".cmake_build.build_config.json"

    def __init__(self, filename=None, data=None, cmake_generator=None,
                 cmake_toolchain=None, **kwargs):
        # -- OPTIONAL OVERRIDE:
        the_data = data or {}
        cmake_defines = the_data.get("cmake_defines", [])
        if cmake_generator:
            the_data["cmake_generator"] = cmake_generator
        if cmake_toolchain:
            the_data["cmake_toolchain"] = cmake_toolchain
        # -- SETUP/INIT: BASE-CLASSES
        CMakeProjectData.__init__(self, data=the_data, **kwargs)
        PersistentData.__init__(self, filename, data=self.data)

    # def make_data(self):
    #     data = self.data.copy()
    #     cmake_defines = data.get("cmake_defines", None)
    #     if cmake_defines is not None:
    #         data["cmake_defines"] = [
    #             {name: value} for name, value in cmake_defines.items()
    #         ]
    #     return data

    # @classmethod
    # def load(cls, filename):
    #     persistent_object = PersistentData.load(filename)
    #     # persistent_object.normalize_data()
    #     return persistent_object


class BuildConfig(CMakeProjectData):
    """Represent the configuration data related to a build-configuration.


    .. code-block:: YAML

        # -- FILE: cmake_build.config.yaml
        ...
        build_configs:
          - Linux_arm64_Debug:
              cmake_build_type: Debug
              cmake_toolchain: cmake/toolchain/linux_gcc_arm64.cmake
              cmake_defines:
                - CMAKE_BUILD_TYPE=Debug
            - cmake_init_args: --warn-uninitialized --check-system-vars

          - Linux_arm64_Release:
              cmake_build_type: MinSizeRel
              cmake_toolchain: cmake/toolchain/linux_gcc_arm64.cmake
              cmake_generator: ninja

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
            cmake_generator = self.stored_data.cmake_generator or \
                              cmake_generator_default
        self.cmake_generator = cmake_generator
        self.cmake_toolchain = cmake_toolchain
        self.cmake_install_prefix = self.replace_placeholders(self.cmake_install_prefix)
        # XXX self.cmake_defines = self.replace_placeholders(self.cmake_defines)
        self._dirty = True

    def reset_dirty(self):
        self._dirty = False

    def exists(self):
        return self.project_dir.isdir()

    def replace_placeholders(self, value):
        if value:
            # -- REPLACE PLACEHOLDERS:
            if isinstance(value, str):
                value = value.replace("{BUILD_CONFIG}", self.build_config.name) \
                         .replace("{CMAKE_BUILD_TYPE}",
                                  self.current_data.cmake_build_type) \
                         .replace("{CMAKE_PROJECT_DIR}", self.project_dir) \
                         .replace("{CMAKE_PROJECT_BUILD_DIR}", self.project_build_dir) \
                         .replace("{CWD}", os.getcwd()) \
                         .replace("{HOME}", os.environ.get("HOME", "__UNKOWN_HOME"))
            elif isinstance(value, dict):
                data = value
                for name, value in data.items():
                    value2 = self.replace_placeholders(value)
                    if value2 != value:
                        data[name] = value
                value = data
        return value

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

    @property
    def cmake_install_prefix(self):
        return self.current_data.cmake_install_prefix

    @cmake_install_prefix.setter
    def cmake_install_prefix(self, value):
        if value:
            # -- REPLACE PLACEHOLDERS:
            value = self.replace_placeholders(value)

        # print("XXX cmake_install_prefix= {0}".format(value))
        self.current_data.cmake_install_prefix = value
        self.dirty = True

    def _on_cmake_build_data_loaded(self, data):
        """Can be overridden."""
        pass

    def update_from_build_config(self):
        """Update attr:`current_data` from the :attr:`build_config` data."""
        self.current_data.cmake_toolchain = self.build_config.cmake_toolchain
        self.current_data.cmake_generator = self.build_config.cmake_generator
        self.current_data.cmake_build_type = self.build_config.cmake_build_type
        self.current_data.cmake_install_prefix = self.build_config.cmake_install_prefix
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
        if (not cmake_build_data_filename.exists() or store_always
                or (self.current_data != self.stored_data)):
            # -- STORE DATA (persistently):
            self.current_data.save(self.cmake_build_data_filename)
            self.stored_data = self.current_data.copy()
        self.dirty = False

    def make_cmake_init_options(self, cmake_generator=None):
        cmake_toolchain = self.current_data.cmake_toolchain
        cmake_generator = self.current_data.cmake_generator
        cmake_install_prefix = self.replace_placeholders(
            self.build_config.cmake_install_prefix)
        cmake_defines = self.replace_placeholders(self.build_config.cmake_defines)
        cmdline = cmake_cmdline(args=self.build_config.cmake_args,
                                defines=cmake_defines,
                                generator=cmake_generator,
                                toolchain=cmake_toolchain,
                                build_type=self.build_config.cmake_build_type,
                                install_prefix=cmake_install_prefix)
        return cmdline

    def make_cmake_update_options(self, **more_defines):
        cmake_toolchain = self.current_data.cmake_toolchain
        cmake_install_prefix = self.replace_placeholders(
            self.build_config.cmake_install_prefix)
        cmake_defines = self.replace_placeholders(self.build_config.cmake_defines)
        # print("XXX cmake_defines: %r" % self.build_config.cmake_defines)
        cmdline = cmake_cmdline_define_options(defines=cmake_defines,
                                               toolchain=cmake_toolchain,
                                               build_type=self.build_config.cmake_build_type,
                                               install_prefix=cmake_install_prefix,
                                               **more_defines)
        return cmdline

    def has_cmake_build_data_file(self):
        return self.cmake_build_data_filename.exists()

    @property
    def initialized(self):
        verbose = CMAKE_BUILD_VERBOSE
        if verbose:
            print("initialized.project_build_dir:     {0} (exists: {1})".format(
                self.project_build_dir.relpath(),
                self.project_build_dir.exists()
            ))
            print("initialized.cmake_build_data_file: {0} (exists: {1})".format(
                self.cmake_build_data_filename.relpath(),
                self.has_cmake_build_data_file()
            ))
        return self.project_build_dir.exists() and self.has_cmake_build_data_file()

    def needs_reinit(self):
        return ((self.current_data != self.stored_data) or
                not self.cmake_build_data_filename.exists())
                # -- MAYBE: or self.dirty

    def needs_update(self):
        """Indicates if CMake project build_dir needs to be updated."""
        names = [
            "cmake_toolchain", "cmake_build_type", "cmake_install_prefix", "cmake_defines"
        ]
        for name in names:
            if self.current_data[name] != self.stored_data[name]:
                return True
        # -- OTHERWISE:
        return False

    def ensure_init(self, args=None, cmake_generator=None):  # @simplify
        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        needs_update = self.needs_update()
        if self.initialized and not (self.needs_reinit() or needs_update):
            # -- CASE: ALREADY DONE w/ same cmake_generator.
            # pylint: disable=line-too-long
            print("CMAKE-INIT:  {0} (SKIPPED: Initialized with cmake.generator={1})." \
                  .format(project_build_dir, self.cmake_generator))
            return False
        elif self.initialized and needs_update:
            print("CMAKE-INIT:  {0} (NEEDS-UPDATE)".format(project_build_dir))
            self.update()
            return True

        if self.project_build_dir.isdir():
            print("CMAKE-INIT:  {0} (NEEDS-REINIT)".format(project_build_dir))
            self.cleanup()

        cmake_generator = cmake_generator or self.cmake_generator
        ctx = self.ctx
        self.project_build_dir.makedirs_p()
        cmake_init_options = self.make_cmake_init_options(cmake_generator)
        with cd(self.project_build_dir):
            # pylint: disable=line-too-long
            print("CMAKE-INIT:  {0} (using cmake.generator={1})".format(
                project_build_dir, cmake_generator))

            # DISABLED: toolchain, used too late w/ wrong abspath.
            # cmake_init_options = self.make_cmake_init_options(cmake_generator)
            if args:
                cmake_init_options += " {0}".format(make_args_string(args))
            relpath_to_project_dir = self.project_build_dir.relpathto(self.project_dir)
            relpath_to_project_dir = posixpath_normpath(relpath_to_project_dir)
            ctx.run("cmake {options} {relpath}".format(
                options=cmake_init_options, relpath=relpath_to_project_dir))
            print()

            # -- FINALLY: If cmake-init worked, store used cmake_generator.
            self.cmake_generator = cmake_generator
            self.store_cmake_build_data()
        return True

    # -- PROJECT-COMMAND API:
    def cleanup(self):
        if self.project_build_dir.isdir():
            project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
            "CMAKE-CLEANUP: {0}".format(project_build_dir)
            self.project_build_dir.rmtree_p()

    def init(self, args=None, cmake_generator=None):
        """Perform CMake init of the project build directory for this
        build_config.
        """
        return self.ensure_init(args=args, cmake_generator=cmake_generator)

    # -- PRELIMINARY PROTOTYPE:
    def update(self, **data):
        """Update CMake project build directory configuration"""
        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        if not self.initialized:
            print("CMAKE-UPDATE: {0} (SKIPPED: Not initialized yet)".format(project_build_dir))
            return

        # cmake_generator = data.pop("cmake_generator", None)
        # self.ensure_init(cmake_generator=cmake_generator)
        print("CMAKE-UPDATE: {0}".format(project_build_dir))

        # more_cmake_defines = OrderedDict(data.items())
        # cmake_options = cmake_cmdline_define_options([], **data)
        # print("XXX cmake_defines: %r" % self.build_config.cmake_defines)
        cmake_options = self.make_cmake_update_options(**data)
        with cd(self.project_build_dir):
            relpath_to_project_dir = self.project_build_dir.relpathto(self.project_dir)
            relpath_to_project_dir = posixpath_normpath(relpath_to_project_dir)
            self.ctx.run("cmake {0} {1}".format(cmake_options, relpath_to_project_dir))

            # -- FINALLY: If cmake-init worked, store used cmake_generator.
            self.store_cmake_build_data()

    def build(self, args=None, init_args=None, cmake_generator=None,
              ensure_init=True):
        """Triggers the cmake.build step (and delegate to used build-system)."""
        cmake_build_args = ""
        if args:
            cmake_build_args = "-- {0}".format(make_args_string(args))

        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        if ensure_init:
            self.ensure_init(args=init_args, cmake_generator=cmake_generator)
        self.project_build_dir.makedirs_p()
        with cd(self.project_build_dir):
            print("CMAKE-BUILD: {0}".format(project_build_dir))
            self.ctx.run("cmake --build . {0}".format(cmake_build_args).strip())
            print()

    def install(self, prefix=None, cmake_generator=None, use_sudo=False):
        # HINT: cmake --build . --target install
        # self.build(cmake_generator=cmake_generator)
        if prefix:
            # -- HINT: May contain placeholders that are replaced.
            prefix = self.replace_placeholders(prefix)
            # DISABLED: self.cmake_install_prefix = prefix
        self.ensure_init(cmake_generator=cmake_generator)

        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        with cd(self.project_build_dir):
            print("CMAKE-INSTALL: {0}".format(project_build_dir))
            if prefix and prefix != self.cmake_install_prefix:
                # -- PREPARE: cmake configuration w/ new CMAKE_INSTALL_PREFIX
                print("CMAKE-INSTALL: Use CMAKE_INSTALL_PREFIX={0}".format(prefix))
                cmake_update_command = "cmake -DCMAKE_INSTALL_PREFIX={0} {1}".format(
                    prefix, posixpath_normpath(self.project_dir.relpath()))
                self.ctx.run(cmake_update_command)
                self.cmake_install_prefix = prefix
                # DISABLED: self.store_cmake_build_data()

            # print("CMAKE-INSTALL: {0} (using: CMAKE_INSTALL_PREFIX={1})".format(
            #    project_build_dir, self.cmake_install_prefix))
            cmake_install_command = "cmake --build . --target install"
            # cmake_install_command = "cmake --build . -- install"
            if use_sudo:
                self.ctx.sudo(cmake_install_command)
            else:
                self.ctx.run(cmake_install_command)
            print()


    def clean(self, args=None, init_args=None):
        """Clean the build artifacts (but: preserve CMake init)"""
        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        if not self.initialized:
            print("CMAKE-CLEAN: {0} (SKIPPED: not initialized yet)".format(
                project_build_dir))
            return

        # -- ALTERNATIVE: self.build(args="clean", ensure_init=False)
        self.ensure_init(args=init_args)
        print("CMAKE-CLEAN: {0}".format(project_build_dir))
        cmake_clean_args = "clean"
        if args:
            clean_args = make_args_string(args)
            cmake_clean_args = "clean {0}".format(clean_args)
        with cd(self.project_build_dir):
            self.ctx.run("cmake --build . -- {0}".format(cmake_clean_args))

    def reinit(self, args=None):
        self.cleanup()
        self.init(args=args)

    def rebuild(self, args=None, init_args=None):
        if self.REBUILD_USE_DEEP_CLEANUP:
            self.cleanup()

        self.clean(init_args=init_args)
        self.build(args=args, ensure_init=True)

    def redo(self, args=None, init_args=None):
        self.reinit(args=init_args)
        self.rebuild(args=args)

    def ctest(self, args=None, init_args=None, verbose=False):
        """Run ctest on CMake project.

        :param args: CTest args to use (as string)
        :param verbose: If true, run tests in verbose mode.
        """
        ctest_args = ""
        if verbose:
            args = ["--verbose", args or ""]
        if args:
            ctest_args = make_args_string(args)

        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        self.ensure_init(args=init_args)
        self.project_build_dir.makedirs_p()
        with cd(self.project_build_dir):
            print("CMAKE-TEST:  {0}".format(project_build_dir))
            self.ctx.run("ctest {0}".format(ctest_args))
            print()

    def test(self, args=None, init_args=None, verbose=False):
        """Run tests of CMake project (by using ctest).

        :param args: CTest args to use (as string)
        :param verbose: If true, run tests in verbose mode.
        """
        self.ctest(args=args, init_args=init_args, verbose=verbose)


# ---------------------------------------------------------------------------
# SPECIAL CASES: CMAKE PROJECTS WITH FAILURE SYNDROME(s)
# ---------------------------------------------------------------------------
class CMakeProjectWithSyndrome(object):
    """Common base class for :class:`CMakeProject`(s) that have a syndrome.

    Examples are:

    * :attr:`project_dir` directory does not exist
    * No "CMakeLists.txt" file exists in the :attr:`project_dir` directory
    """
    SYNDROME = "Faulty cmake.project"
    FAILURE_TEMPLATE = "{reason}"

    def __init__(self, project_dir=None, syndrome=None):
        self.project_dir = Path(project_dir or ".").abspath()
        self.syndrome = syndrome or self.SYNDROME

    def relpath_to_project_dir(self, start="."):
        return posixpath_normpath(self.project_dir.relpath(start))

    def fail(self, reason):
        raise NiceFailure(reason=reason,
                          template=self.FAILURE_TEMPLATE)

    def warn(self, reason):
        print(reason)

    # -- PROJECT-COMMAND API:
    def cleanup(self):
        self.warn("CMAKE-CLEANUP: {0} (SKIPPED: {1})".format(
                  self.relpath_to_project_dir(), self.syndrome))

    def init(self, **kwargs):
        self.fail("CMAKE-INIT: {0} (SKIPPED: {1})".format(
                  self.relpath_to_project_dir(), self.syndrome))

    def build(self, **kwargs):
        self.fail("CMAKE-BUILD: {0} (SKIPPED: {1})".format(
                    self.relpath_to_project_dir(), self.syndrome))

    def clean(self, **kwargs):
        self.warn("CMAKE-CLEAN: {0} (SKIPPED: {1})".format(
                  self.relpath_to_project_dir(), self.syndrome))

    def reinit(self, args=None):
        self.cleanup()
        self.init(args=args)

    def rebuild(self, args=None, init_args=None):
        self.clean(init_args=init_args)
        self.build(args=args, ensure_init=True)

    def redo(self, args=None, init_args=None):
        self.reinit(args=init_args)
        self.rebuild(args=args)

    def ctest(self, args=None, init_args=None):
        self.fail("CMAKE-TEST: {0} (SKIPPED: {1})".format(
                  self.relpath_to_project_dir(), self.syndrome))

    def test(self, args=None, init_args=None):
        self.ctest(args=args, init_args=init_args)


class CMakeProjectWithoutProjectDirectory(CMakeProjectWithSyndrome):
    SYNDROME = "cmake.project directory does not exist"


class CMakeProjectWithoutCMakeListsFile(CMakeProjectWithSyndrome):
    """Used if the "CMakeLists.txt" file is missing in the :attr:`project_dir`"""
    SYNDROME = "not a cmake.project (missing: CMakeLists.txt file)"


# ---------------------------------------------------------------------------
# COMPOSITE RUNNER: For many cmake projects
# ---------------------------------------------------------------------------
class CMakeBuildRunner(object):
    """Build runner for many CMake projects (composite)."""
    def __init__(self, cmake_projects=None, target=None):
        self.cmake_projects = cmake_projects or []
        self.default_target = target or "build"

    def execute_target(self, target, args=None, init_args=None, **kwargs):
        target = target or self.default_target
        for cmake_project in self.cmake_projects:
            project_target_func = getattr(cmake_project, target, None)
            if project_target_func:
                if args or init_args or kwargs:
                    if target == "init":
                        project_target_func(args=args, **kwargs)
                    else:
                        project_target_func(args=args, init_args=init_args, **kwargs)
                else:
                    project_target_func()
            else:
                print("CMAKE-BUILD: Skip target={0} for {1} (not-supported)".format(
                    target, posixpath_normpath(cmake_project.project_dir)
                ))

    def __call__(self, target=None):
        self.execute_target(target)

    def set_cmake_generator(self, cmake_generator=None):
        # -- OVERRIDE: cmake_generator
        for cmake_project in self.cmake_projects:
            cmake_project.cmake_generator = cmake_generator

    def run(self, target=None):
        self.execute_target(target)

    def init(self, args=None):
        self.execute_target("init", args=args)

    def build(self, args=None, init_args=None):
        self.execute_target("build", args=args, init_args=init_args)

    def test(self, args=None, init_args=None):
        self.execute_target("test", args=args, init_args=init_args)

    def reinit(self, args=None):
        self.execute_target("cleanup")
        self.execute_target("init", args=args)

    def rebuild(self, args=None, init_args=None):
        self.execute_target("rebuild", args=args, init_args=init_args)

    def clean(self, args=None):
        self.execute_target("clean", args=args)

    def cleanup(self):
        self.execute_target("cleanup")
