# -*- coding: UTF-8 -*-
# pylint: disable=no-value-for-parameter, invalid-name
# pylint: disable=useless-object-inheritance # RELATED-TO: Python3
# pylint: disable=redefined-builtin,
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
from invoke.util import cd
from path import Path
from cmake_build.config import CMakeProjectPersistConfig, BuildConfig
from .cmake_util import CMAKE_DEFAULT_GENERATOR, CPACK_GENERATOR, \
    make_build_dir_from_schema, cmake_cmdline, cmake_cmdline_define_options
from .exceptions import NiceFailure
from .pathutil import posixpath_normpath


# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
CMAKE_BUILD_VERBOSE = (os.environ.get("CMAKE_BUILD_VERBOSE", None) == "yes")
CMAKE_PARALLEL_UNSET = -1


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
# CMAKE PROJECT CLASSES:
# -----------------------------------------------------------------------------
class CMakeProject(object):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """CMake project entity that represents a
    CMake project with one build configuration (one build_dir).

    RESPONSIBILITIES:
    * Can initialize a CMake project (and its build_dir)
    * Can cleanup/remove the CMake project build_dir (and its build artifacts)
    * Stores cmake-init configuration data in the build_dir
    * Can detect when the cmake-init configuration data changes
      and automatically triggers a cmake-reinit of the build_dir
      (example: another toolchain is used, cmake-init definitions change, ...)

    The attributes are:

    .. attribute:: config

        Current configuration data of this CMake project.
        It describes the configuration data that should be used.
        It may differ from :attr:`_build_config` and :attr:`_stored_config`.

        The attr:`config` is stored in :attr:`_stored_config`
        (and its persistent config-file) if it differs from it.

    .. attribute:: _stored_config

        Stored configuration data of this CMake project (in cmake_project.build_dir).
        It describes the configuration that was last used to (re-)init/update
        this CMake project for building it.

    .. attribute:: _build_config

        Build configuration that comes from the "cmake_build.yaml" config-file.
        It describes the pre-canned, intended configuration of this CMake project
        (for this build-config).

    """
    CMAKE_BUILD_DATA_FILENAME = ".cmake_build.build_config.json"
    CMAKE_BUILD_TYPE_DEFAULT = "Debug"
    CMAKE_CONFIG_OVERRIDES_CMAKE_BUILD_TYPE = False
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

        config_name = build_config.name
        cmake_generator_default = build_config.cmake_generator
        cmake_toolchain = build_config.cmake_toolchain

        self.ctx = ctx
        self.project_dir = project_dir
        self.project_build_dir = Path(project_build_dir).abspath()
        self.config = None
        self._build_config = build_config
        self._stored_config = None
        self._stored_cmake_generator = None
        self._dirty = True
        self._placeholder_map = {}
        self.load_config()
        self.update_from_initial_config(build_config)
        self.config.name = config_name
        if not cmake_generator:
            # -- INHERIT: Stored cmake_generator, if it is not overridden.
            cmake_generator = self._stored_config.cmake_generator or \
                              cmake_generator_default
        self.config.cmake_generator = cmake_generator
        self.config.cmake_toolchain = cmake_toolchain
        self.cmake_install_prefix = self.replace_placeholders(
            self.cmake_install_prefix)
        self.cmake_config_overrides_cmake_build_type = \
            self.CMAKE_CONFIG_OVERRIDES_CMAKE_BUILD_TYPE
        # MAYBE:
        # self.cmake_defines = self.replace_placeholders(self.cmake_defines)
        self._dirty = True

    def _make_placeholder_dict(self):
        username = None
        for envname in ("USER", "LOGNAME", "USERNAME"):
            username = os.environ.get(envname)
            if username:
                break
        if not username:
            username = "nobody"

        placeholders = {
            "BUILD_CONFIG": self.config.name,
            "CMAKE_BUILD_TYPE": self.config.cmake_build_type,
            "CMAKE_PROJECT_DIR": self.project_dir,
            "CMAKE_PROJECT_BUILD_DIR": self.project_build_dir,
            "CWD": os.getcwd(),
            "HOME": os.environ.get("HOME", "__UNKOWN_HOME"),
            "USER": username,
        }
        return placeholders

    def reset_dirty(self):
        self._dirty = False

    def reset_config(self, cmake_generator=None):
        """Reset the CMake project configuration."""
        if not cmake_generator:
            cmake_generator = self.config.cmake_generator

        config_name = self.config.name  # PRESERVE: config.name
        assert config_name == self._build_config.name
        self._placeholder_map = {}
        self.load_config()
        self.update_from_initial_config(self._build_config)
        self.config.name = config_name
        if cmake_generator:
            self.config.cmake_generator = cmake_generator
        if self._stored_cmake_generator and not self._stored_config.cmake_generator:
            # -- RESTORE: stored_cmake_generator info
            self._stored_config.cmake_generator = self._stored_cmake_generator
            self._stored_config.save(self.stored_config_filename)

    def exists(self):
        return self.project_dir.isdir()

    def replace_placeholders(self, value):
        if not self._placeholder_map:
            self._placeholder_map = self._make_placeholder_dict()
        placeholders = self._placeholder_map

        if value:
            # -- REPLACE PLACEHOLDERS:
            # pylint: disable=line-too-long
            if isinstance(value, str):
                if "{" in value:
                    try:
                        new_value = value.format(**placeholders)
                        value = new_value
                    except KeyError as e:
                        print("UNKNOWN-PLACEHOLDER: %s in value: %s" % (e, value))
                        raise

                # value = value.replace("{BUILD_CONFIG}", self.config.name) \
                #          .replace("{CMAKE_BUILD_TYPE}",
                #                   self.config.cmake_build_type) \
                #          .replace("{CMAKE_PROJECT_DIR}", self.project_dir) \
                #          .replace("{CMAKE_PROJECT_BUILD_DIR}", self.project_build_dir) \
                #          .replace("{CWD}", os.getcwd()) \
                #          .replace("{HOME}", os.environ.get("HOME", "__UNKOWN_HOME"))
            elif isinstance(value, dict):
                # pylint: disable=redefined-argument-from-local
                data = value
                for name, item_value in data.items():
                    new_value = self.replace_placeholders(item_value)
                    if new_value != item_value:
                        data[name] = new_value
                value = data
            elif isinstance(value, list):
                data = value
                for index, item_value in enumerate(data):
                    new_value = self.replace_placeholders(item_value)
                    if new_value != item_value:
                        data[index] = new_value
                value = data
        return value

    @property
    def dirty(self):
        return self._dirty or (self.config != self._stored_config)
        # MAYBE: not self.stored_data.exists()

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    @property
    def stored_config_filename(self):
        return self.project_build_dir/self.CMAKE_BUILD_DATA_FILENAME

    @property
    def cmake_install_prefix(self):
        return self.config.cmake_install_prefix

    @cmake_install_prefix.setter
    def cmake_install_prefix(self, value):
        if value:
            # -- REPLACE PLACEHOLDERS:
            value = self.replace_placeholders(value)

        # print("XXX cmake_install_prefix= {0}".format(value))
        self.config.cmake_install_prefix = value
        self.dirty = True

    def _on_config_loaded(self, data):
        """Can be overridden."""

    def update_from_initial_config(self, build_config):
        """Update :attr:`config` from the :param:`build_config` data."""
        # XXX-WORKMARK: Update or merge needed here ?!?
        if not self.config:
            self.load_config()
        if False:   # pylint: disable=using-constant-test
            self.config.cmake_toolchain = build_config.cmake_toolchain
            self.config.cmake_generator = build_config.cmake_generator
            self.config.cmake_build_type = build_config.cmake_build_type
            self.config.cmake_install_prefix = build_config.cmake_install_prefix
            self.config.cmake_defines.update(build_config.cmake_defines.items())
            self.config.cmake_args = build_config.cmake_args
        for name, value in build_config.items():
            current_value = self.config.get(name)
            if not current_value and value:
                self.config[name] = value
        # XXX print("XXX config: %r" % self.config.data)
        # XXX print("XXX build_config: %r" % build_config.data)
        self.config.normalize_data()
        # print("XXX cmake_project.config= %r" % self.config.data)

    def load_config(self):
        """Load the CMake project build configuration from the persistent file
        in the ``cmake_project.project_build_dir``.
        """
        stored_config_filename = self.stored_config_filename
        file_exists = stored_config_filename.exists()
        try:
            stored_config = CMakeProjectPersistConfig.load(stored_config_filename)
        except ValueError:
            print('OOPS: ParseError in "{0}" (IGNORED)'.format(
                stored_config_filename.relpath()))
            stored_config = CMakeProjectPersistConfig()

        self._on_config_loaded(stored_config)
        self._stored_config = stored_config
        if stored_config.cmake_generator:
            self._stored_cmake_generator = self._stored_config.cmake_generator
        self.config = stored_config.copy()
        self.reset_dirty()
        if not file_exists:
            # -- ENFORCE: Persistent config-file will be written.
            self.dirty = True

    def store_config(self):
        """Store the current CMake project configuration to the persistent file
        in the ``cmake_project.project_build_dir``.
        """
        stored_config_filename = self.stored_config_filename
        if (not stored_config_filename.exists() or
                self.config != self._stored_config):
            # -- STORE CONFIG-DATA (persistently):
            self.config.save(self.stored_config_filename)
            self._stored_config = self.config.copy()
        self.dirty = False

    def make_cmake_init_options(self, cmake_generator=None, config=None):
        if cmake_generator is None:
            cmake_generator = self.config.cmake_generator
        cmake_toolchain = self.config.cmake_toolchain
        cmake_install_prefix = self.replace_placeholders(
            self.config.cmake_install_prefix)
        cmake_defines = self.replace_placeholders(self.config.cmake_defines)
        cmdline = cmake_cmdline(args=self.config.cmake_init_args,
                                defines=cmake_defines,
                                generator=cmake_generator,
                                toolchain=cmake_toolchain,
                                build_type=self.config.cmake_build_type,
                                config=config,
                                install_prefix=cmake_install_prefix)
        return cmdline

    def make_cmake_configure_options(self, **more_defines):
        # pylint: disable=line-too-long
        cmake_toolchain = self.config.cmake_toolchain
        cmake_install_prefix = self.replace_placeholders(
            self.config.cmake_install_prefix)
        cmake_defines = self.replace_placeholders(self.config.cmake_defines)
        # print("XXX cmake_defines: %r" % self.config.cmake_defines)
        cmdline = cmake_cmdline_define_options(defines=cmake_defines,
                                               toolchain=cmake_toolchain,
                                               build_type=self.config.cmake_build_type,
                                               install_prefix=cmake_install_prefix,
                                               **more_defines)
        return cmdline

    def has_stored_config_file(self):
        return self.stored_config_filename.exists()

    @property
    def initialized(self):
        """Indicates if CMake project is initialized.
        This means:
        * CMake project build_dir exists
        * store_config file exists in CMake project build_dir
        """
        # verbose = CMAKE_BUILD_VERBOSE
        # if verbose:
        #     self.diagnose_initialized_problems()
        return self.project_build_dir.exists() and self.has_stored_config_file()

    def diagnose_initialized_problems(self):
        # pragma: nocover
        print("initialized.project_build_dir:     {0} (exists: {1})".format(
            self.project_build_dir.relpath(),
            self.project_build_dir.exists()
        ))
        print("initialized.cmake_build_data_file: {0} (exists: {1})".format(
            self.stored_config_filename.relpath(),
            self.has_stored_config_file()
        ))

    def needs_reinit(self):
        """Indicates if the cmake_project.build_dir should be recreated.
        This is required (or better) when the cmake.generator changes.
        """
        current_cmake_generator = self.config.get("cmake_generator")
        stored_cmake_generator = self._stored_config.get("cmake_generator")
        return ((current_cmake_generator != stored_cmake_generator) or
                not self.has_stored_config_file())

    def needs_update(self):
        """Indicates if CMake project build_dir needs to be updated."""
        return not self.config.same_as(self._stored_config,
                                       excluded=["cmake_generator"])

    def needs_conan(self):
        """Detects if conan is needed."""
        return any([Path(self.project_dir/conanfile).exists()
                    for conanfile in ("conanfile.py", "conanfile.txt")])

    def ensure_init(self, args=None, cmake_generator=None, config=None):  # @simplify
        # pylint: disable=line-too-long, disable=no-else-return
        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        if self.initialized:
            # -- CASE: cmake_project.build_dir exists and stored_config file exists
            if config and self.cmake_config_overrides_cmake_build_type:
                self.config.cmake_build_type = config
            needs_update = self.needs_update()
            needs_reinit = self.needs_reinit()
            if not (needs_reinit or needs_update):
                # -- CASE: ALREADY DONE w/ same cmake_generator.
                print("CMAKE-INIT:  {0} (SKIPPED: Initialized with cmake.generator={1})." \
                      .format(project_build_dir, self.config.cmake_generator))
                return False
            elif needs_update and not needs_reinit:
                print("CMAKE-INIT:  {0} (NEEDS-UPDATE, using cmake.generator={1})"\
                      .format(project_build_dir, self.config.cmake_generator))
                self.configure()
                return True

        # -- CASE: NOT INITIALIZED or NEEDS REINIT
        if self.project_build_dir.isdir():
            print("CMAKE-INIT:  {0} (NEEDS-REINIT)".format(project_build_dir))
            self.cleanup()

        cmake_generator = cmake_generator or self.config.cmake_generator
        ctx = self.ctx
        self.project_build_dir.makedirs_p()
        cmake_init_options = self.make_cmake_init_options(cmake_generator,
                                                          config=config)
        with cd(self.project_build_dir):
            # pylint: disable=line-too-long
            print("CMAKE-INIT:  {0} (using cmake.generator={1})".format(
                project_build_dir, cmake_generator))

            if args:
                cmake_init_options += " {0}".format(make_args_string(args))
            relpath_to_project_dir = self.project_build_dir.relpathto(self.project_dir)
            relpath_to_project_dir = posixpath_normpath(relpath_to_project_dir)
            if self.needs_conan():
                conan_build_type = config or self.config.cmake_build_type
                ctx.run("conan install {relpath} -s build_type={build_type}".format(
                        relpath=relpath_to_project_dir,
                        build_type=conan_build_type))
            ctx.run("cmake {options} {relpath}".format(
                    options=cmake_init_options,
                    relpath=relpath_to_project_dir))
            print()

            # -- FINALLY: If cmake-init worked, store used cmake_generator.
            self.config.cmake_generator = cmake_generator
            self.store_config()
            self._stored_cmake_generator = cmake_generator
        return True

    # -- PROJECT-COMMAND API:
    def cleanup(self):
        """Remove cmake_project.project_build_dir"""
        verbose = False
        if self.project_build_dir.isdir():
            project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
            if verbose:
                # pragma: nocover
                print("CMAKE-CLEANUP: {0}".format(project_build_dir))
            self.project_build_dir.rmtree_p()
            self._stored_cmake_generator = None

    def remove_stored_config(self):
        """Remove the persistent data-file for the stored_config (if exists)."""
        stored_config_filename = self.stored_config_filename
        if stored_config_filename.exists():
            stored_config_filename.remove()
            self._stored_cmake_generator = self._stored_config.cmake_generator

    def init(self, args=None, cmake_generator=None, config=None):
        """Perform CMake init of the project build directory for this
        build_config.
        """
        if not args:
            args = self.config.cmake_init_args
        return self.ensure_init(args=args, cmake_generator=cmake_generator,
                                config=config)

    # -- PRELIMINARY PROTOTYPE:
    def configure(self, **data):
        """Update CMake project build directory configuration"""
        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        if not self.initialized:
            print("CMAKE-UPDATE: {0} (SKIPPED: Not initialized yet)".format(
                project_build_dir))
            return

        for name, value in data.items():
            self.config.cmake_defines[name] = value

        # cmake_generator = data.pop("cmake_generator", None)
        # self.ensure_init(cmake_generator=cmake_generator)
        print("CMAKE-CONFIGURE: {0}".format(project_build_dir))

        # more_cmake_defines = OrderedDict(data.items())
        # cmake_options = cmake_cmdline_define_options([], **data)
        # print("XXX cmake_defines: %r" % self.config.cmake_defines)
        # pylint: disable=line-too-long
        cmake_options = self.make_cmake_configure_options(**data)
        with cd(self.project_build_dir):
            relpath_to_project_dir = self.project_build_dir.relpathto(self.project_dir)
            relpath_to_project_dir = posixpath_normpath(relpath_to_project_dir)
            self.ctx.run("cmake {0} {1}".format(cmake_options, relpath_to_project_dir))

            # -- FINALLY: If cmake-init worked, store used cmake_generator.
            self.store_config()

    # -- BACKWARD-COMPATIBLE:
    # def update(self, **data):
    #     self.configure(**data)

    def build(self, args=None, options=None, init_args=None,
              cmake_generator=None, config=None, ensure_init=True,
              target=None, parallel=CMAKE_PARALLEL_UNSET,
              clean_first=False, verbose=False):
        # pylint: disable=too-many-arguments
        """Triggers the cmake.build step (and delegate to used build-system).

        :param args:    List of CMake build args to use (passed to build system).
        :param options: List of CMake build options to use.
        :param init_args: List of CMake init args passed to init command.
        :param cmake_generator: Name of cmake.generator to use.
        :param ensure_init:  Indicates if initialized state should be checked.
        :param target:  Name of other target for build command (optional).
        :param parallel: Number of parallel build jobs to use (optional).
        :param clean_first: Indicates if build uses --clean-first option.
        :param verbose: Use verbose build mode or not (optional).
        """
        needs_store_config = False
        cmake_build_args = ""
        cmake_build_options = ""
        options = options or []
        assert isinstance(options, list)
        if config:
            options.append("--config {0}".format(config))
        if target:
            options.append("--target {0}".format(target))
        if parallel == CMAKE_PARALLEL_UNSET or parallel < 0:
            # -- INHERIT: From last run.
            parallel = self.config.cmake_parallel
        if parallel >= 0:
            self.config.cmake_parallel = parallel  # -- REMEMBER: Last value.
            needs_store_config = True
            if parallel == 0:
                options.append("--parallel")
            elif  parallel >= 2:
                options.append("--parallel {0}".format(parallel))

        if clean_first:
            options.append("--clean-first")
        if verbose:
            options.append("--verbose")

        if options:
            cmake_build_options = " ".join(options or [])
        if args:
            cmake_build_args = "-- {0}".format(make_args_string(args))

        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        if ensure_init:
            self.ensure_init(args=init_args, cmake_generator=cmake_generator,
                             config=config)
        if needs_store_config:
            # -- ENSURE: Initial stored_config is kept after INIT-STEP.
            self.store_config()

        self.project_build_dir.makedirs_p()
        with cd(self.project_build_dir):
            print("CMAKE-BUILD: {0}".format(project_build_dir))
            self.ctx.run("cmake --build . {0} {1}".format(
                cmake_build_options, cmake_build_args).strip())
            print()

    def install(self, prefix=None, cmake_generator=None, config=None,
                use_sudo=False):
        # pylint: disable=line-too-long
        # HINT: cmake --build . --target install
        # self.build(cmake_generator=cmake_generator)
        if prefix:
            # -- HINT: May contain placeholders that are replaced.
            prefix = self.replace_placeholders(prefix)
            # DISABLED: self.cmake_install_prefix = prefix

        cmake_config = ""
        if config:
            cmake_config = "--config {0}".format(config)

        self.ensure_init(cmake_generator=cmake_generator, config=config)

        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        with cd(self.project_build_dir):
            print("CMAKE-INSTALL: {0}".format(project_build_dir))
            if prefix and prefix != self.cmake_install_prefix:
                # -- PREPARE: cmake configuration w/ new CMAKE_INSTALL_PREFIX
                print("CMAKE-INSTALL: Use CMAKE_INSTALL_PREFIX={0}".format(prefix))
                cmake_configure_command = "cmake -DCMAKE_INSTALL_PREFIX={0} {1}".format(
                    prefix, posixpath_normpath(self.project_dir.relpath()))
                self.ctx.run(cmake_configure_command)
                self.cmake_install_prefix = prefix
                # DISABLED: self.store_config()

            # print("CMAKE-INSTALL: {0} (using: CMAKE_INSTALL_PREFIX={1})".format(
            #    project_build_dir, self.cmake_install_prefix))
            cmake_install = "cmake --build . {0} --target install".format(cmake_config)
            # cmake_install_command = "cmake --build . {0} -- install".format(cmake_config)
            if use_sudo:
                self.ctx.sudo(cmake_install)
            else:
                self.ctx.run(cmake_install)
            print()

    def pack(self, format=None, package_dir=None, cpack_config=None,
             source_bundle=False, vendor=None, config=None, verbose=False):
        # pylint: disable=unused-argument   # RELATED-TO: config (PREPARED)
        # pylint: disable=line-too-long
        """Run cpack command to package:

         * source-code archives
         * binary archives
         * packages (for package managers)
         * installers, installation packages

         :param format: CPack generator format, like: ZIP, TGZ, ... (CPACK_GENERATOR).
         :param package_dir: Override package directory (CPACK_PACKAGE_DIRECTORY).
         :param source_bundle: Create source-bundle (if true).
         :param vendor: Override package vendor name (CPACK_PACKAGE_VENDOR).
         :param verbose: Enable cpack verbose mode (optional, default=off).
         """
        format = format or CPACK_GENERATOR
        options = []
        if package_dir:
            # -- OVERRIDE: CPACK_PACKAGE_DIRECTORY
            # Issue #19412 <https://gitlab.kitware.com/cmake/cmake/issues/19412>
            # package_dir must be an absolute-path
            package_dir = Path(package_dir)
            if not package_dir.isabs():
                package_dir = Path(self.project_build_dir / package_dir).abspath()
            options.append("-B {0}".format(package_dir))
        if vendor:
            # -- OVERRIDE: CPACK_PACKAGE_VENDOR
            options.append("--vendor '{0}'".format(vendor))
        if verbose:
            options.append("--verbose")
        cpack_options = " ".join(options)

        # -- CPACK-CONFIG OPTION: --config <CPACK_CONFIG_FILE>
        cpack_config = cpack_config or "CPackConfig.cmake"
        if source_bundle:
            cpack_config = "CPackSourceConfig.cmake"

        self.ensure_init()
        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        with cd(self.project_build_dir):
            print("CMAKE-PACK: {0} (using cpack.generator={1})".format(
                project_build_dir, format))
            self.ctx.run("cpack -G {0} --config {1} {2}".format(
                format, cpack_config, cpack_options).strip())


    def clean(self, args=None, options=None, init_args=None, config=None):
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

        options = options or []
        if config:
            options.append("--config {0}".format(config))
        cmake_options = " ".join(options)

        # pylint: disable=line-too-long
        with cd(self.project_build_dir):
            self.ctx.run("cmake --build . {0} -- {1}".format(cmake_options, cmake_clean_args))

    def reinit(self, args=None, config=None):
        self.cleanup()
        self.reset_config()
        self.init(args=args, config=config)

    def rebuild(self, args=None, options=None, init_args=None, config=None,
                parallel=CMAKE_PARALLEL_UNSET, **kwargs):
        cleanup_build_dir = kwargs.pop("cleanup", False)
        if cleanup_build_dir or self.REBUILD_USE_DEEP_CLEANUP:
            self.cleanup()

        self.clean(init_args=init_args, config=config)
        self.build(args=args, options=options, ensure_init=True,
                   config=config, parallel=parallel)

    def redo(self, args=None, options=None, init_args=None, config=None, **kwargs):
        self.reinit(args=init_args, config=config)
        self.rebuild(args=args, options=options, config=config, **kwargs)

    def ctest(self, args=None, init_args=None, config=None, verbose=False):
        """Run ctest on CMake project.

        :param args: CTest args to use (as string)
        :param verbose: If true, run tests in verbose mode.
        """
        ctest_args = ""
        args = args or []
        if config:
            args.append("-C {0}".format(config))
        if verbose:
            args.insert(0, "--verbose")
        ctest_args = make_args_string(args)

        project_build_dir = posixpath_normpath(self.project_build_dir.relpath())
        self.ensure_init(args=init_args)
        self.project_build_dir.makedirs_p()
        with cd(self.project_build_dir):
            print("CMAKE-TEST:  {0}".format(project_build_dir))
            self.ctx.run("ctest {0}".format(ctest_args).strip())
            print()

    def test(self, args=None, init_args=None, config=None, verbose=False):
        """Run tests of CMake project (by using ctest).

        :param args: CTest args to use (as string)
        :param verbose: If true, run tests in verbose mode.
        """
        self.ctest(args=args, init_args=init_args, config=config, verbose=verbose)


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
        self.config = CMakeProjectPersistConfig()

    def relpath_to_project_dir(self, start="."):
        return posixpath_normpath(self.project_dir.relpath(start))

    def fail(self, reason):
        raise NiceFailure(reason=reason,
                          template=self.FAILURE_TEMPLATE)

    @staticmethod
    def warn(reason):
        print(reason)

    # -- PROJECT-COMMAND API:
    # pylint: disable=unused-argument
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

    def reinit(self, args=None, config=None, **kwargs):
        self.cleanup()
        self.init(args=args, config=None)

    def rebuild(self, args=None, init_args=None, config=None, **kwargs):
        self.clean(init_args=init_args, config=config)
        self.build(args=args, ensure_init=True)

    def redo(self, args=None, init_args=None, config=None, **kwargs):
        self.reinit(args=init_args, config=config)
        self.rebuild(args=args, config=config)

    def ctest(self, args=None, init_args=None, config=None, **kwargs):
        # pylint: disable=unused-argument
        self.fail("CMAKE-TEST: {0} (SKIPPED: {1})".format(
            self.relpath_to_project_dir(), self.syndrome))

    def test(self, args=None, init_args=None, config=None, **kwargs):
        self.ctest(args=args, init_args=init_args, config=config, **kwargs)

    def install(self, **kwargs):
        self.fail("CMAKE-INSTALL: {0} (SKIPPED: {1})".format(
            self.relpath_to_project_dir(), self.syndrome))

    def pack(self, **kwargs):
        self.fail("CMAKE-PACK: {0} (SKIPPED: {1})".format(
            self.relpath_to_project_dir(), self.syndrome))

    def configure(self, **kwargs):
        self.fail("CMAKE-CONFIGURE: {0} (SKIPPED: {1})".format(
            self.relpath_to_project_dir(), self.syndrome))

    # -- BACKWARD-COMPATIBLE:
    # def update(self, **kwargs):
    #     self.fail("CMAKE-UPDATE: {0} (SKIPPED: {1})".format(
    #         self.relpath_to_project_dir(), self.syndrome))

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
                    elif target in ("install", "pack"):
                        project_target_func(**kwargs)
                    else:
                        project_target_func(args=args, init_args=init_args, **kwargs)
                else:
                    project_target_func()
            else:
                print("CMAKE-BUILD: Skip target={0} for {1} (not-supported)".format(
                    target, posixpath_normpath(cmake_project.project_dir)
                ))

    def __call__(self, target=None, **kwargs):
        self.execute_target(target, **kwargs)

    def set_cmake_generator(self, cmake_generator=None):
        # -- OVERRIDE: cmake_generator
        if cmake_generator is None:
            cmake_generator = CMAKE_DEFAULT_GENERATOR

        for cmake_project in self.cmake_projects:
            cmake_project.config.cmake_generator = cmake_generator

    def run(self, target=None, **kwargs):
        self.execute_target(target, **kwargs)

    def init(self, args=None, config=None):
        self.execute_target("init", args=args, config=config)

    def build(self, args=None, options=None, init_args=None, config=None):
        self.execute_target("build", args=args, options=options,
                            init_args=init_args, config=config)

    def test(self, args=None, init_args=None, config=None):
        self.execute_target("test", args=args, init_args=init_args, config=config)

    def install(self, prefix=None, use_sudo=False, config=None):
        self.execute_target("install", prefix=prefix, use_sudo=use_sudo,
                            config=config)

    def pack(self, format=None, package_dir=None, cpack_config=None,
             source_bundle=None, vendor=None, verbose=False, config=None):
        self.execute_target("pack", format=format, package_dir=package_dir,
                            cpack_config=cpack_config,
                            source_bundle=source_bundle,
                            vendor=vendor,
                            config=config,
                            verbose=verbose)

    def reinit(self, args=None, config=None):
        self.execute_target("cleanup")
        self.execute_target("reset_config")
        self.execute_target("init", args=args, config=config)

    def rebuild(self, args=None, options=None, init_args=None, config=None):
        self.execute_target("rebuild", args=args, options=options,
                            init_args=init_args, config=config)

    def clean(self, args=None, options=None, config=None):
        self.execute_target("clean", args=args, options=options, config=config)

    def cleanup(self):
        self.execute_target("cleanup")
