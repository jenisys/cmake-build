# STATUS: PREPARED (for click support)
# pylint: disable=unused-argument, no-self-use

from __future__ import absolute_import
from collections import OrderedDict
from cmake_build.cmake_util import CMakeDefine, map_build_config_to_cmake_build_type
from cmake_build.persist import PersistentData
from copy import deepcopy


# ---------------------------------------------------------------------------
# PREPARED:
# ---------------------------------------------------------------------------
# CMAKE_BUILD_TARGETS = [
#     "init", "build", "test", "clean", "reinit", "rebuild"
#     # MAYBE: install, cpack, ctest
# ]
#
#
# class CMakeBuildConfig(object):
#     DEFAULT_FILENAME = "cmake-build.config.yaml"
#     DEFAULT_TARGET = "build"
#     CONFIG_DEFAULTS = {
#         "generator": None,
#         "toolchain": None,
#         "build_config": "debug",
#         "build_configs": dict(debug={}, release={}),
#         "projects": [],
#         # DISABLED: "build_config_aliases": dict(default="default"),
#     }
#
#     def __init__(self, filename=None, **kwargs):
#         self.filename = filename or self.DEFAULT_FILENAME
#         self.build_config = None
#         self.project = None
#         self.target = self.DEFAULT_TARGET
#         for name, value in kwargs.items():
#             setattr(self, name, value)
#         self.data = {}
#         self.data.update(self.CONFIG_DEFAULTS)
#
#     def load(self, filename=None):
#         # PREPARED:
#         filename = filename or self.filename
#
#
# class CMakeBuildConfigValidator(object):
#
#     def __init__(self, config):
#         self.config = config
#         self.error_message = None
#
#     @property
#     def build_config(self):
#         return self.config.get("build_config", "debug")
#
#     def check_build_config(self, build_config=None):
#         build_config = build_config or self.build_config
#         okay = build_config in self.config["build_configs"]
#         if not okay:
#             self.error_message = "BAD-BUILD-CONFIG={0}".format(build_config)
#
#     def check_project(self, project):
#         return NotImplemented
#
#     def check(self, config=None):
#         config = config or self.config
#         assert config is not None
#         if self.check_build_config(config.build_config):
#             return False
#         return True


CMAKE_CONFIG_DEFAULTS = {
    "cmake_generator": None,
    "cmake_defines": OrderedDict(),
    "cmake_build_args": [],
    "cmake_init_args": [],
    "cmake_test_args": [],
    "cmake_parallel": 1,    # HINT: parallel=1 means non-parallel mode.
    # "cmake_toolchain": None,
    # "cmake_build_type": None,
    # "cmake_install_prefix": None,
}


# ---------------------------------------------------------------------------
# CMAKE PROJECT CONFIG CLASSES:
# ---------------------------------------------------------------------------
class CMakeDefineProtocol(object):
    CMAKE_DEFINE_ALIASES = {
        "cmake_toolchain": "CMAKE_TOOLCHAIN_FILE",
        "cmake_build_type": "CMAKE_BUILD_TYPE",
        "cmake_install_prefix": "CMAKE_INSTALL_PREFIX",
    }

#     def __init__(self, data):
#         self.data = data
#
#     def get(self, name, default=None):
#         pass
#
#     def __getitem__(self, item):
#         pass
#
#     def __setitem__(self, key, value):
#         pass
#
#     def __contains__(self, item):
#         pass


def unordered_dict_equals(data1, data2):
    if isinstance(data1, OrderedDict):
        data1 = dict(data1)
    if isinstance(data2, OrderedDict):
        data2 = dict(data2)
    return data1 == data2


class CMakeProjectConfig(object):
    DEFAULT_NAME = "default"
    CMAKE_DEFINE_ALIASES = CMakeDefineProtocol.CMAKE_DEFINE_ALIASES

    def __init__(self, data=None, use_defaults=True, **kwargs):
        data_defaults = {}
        if use_defaults:
            data_defaults = deepcopy(CMAKE_CONFIG_DEFAULTS)
            # data_defaults["cmake_defines"].clear()

        self.name = kwargs.pop("name", self.DEFAULT_NAME)
        self.data = data_defaults
        self.data.update(data or {})
        self.data.update(kwargs)
        self.normalize_data()
        # -- CMAKE_DEFINES:
        # self.cmake_toolchain = None
        # self.cmake_build_type = None
        # self.cmake_install_prefix = None

    def normalize_data(self):
        cmake_defines = self.data.get("cmake_defines", None)
        if cmake_defines is None:
            cmake_defines = []
        if not isinstance(cmake_defines, OrderedDict):
            self.data["cmake_defines"] = OrderedDict(cmake_defines)

        # -- REWRITE: data and push info to cmake_defines
        for name, cmake_define_name in self.CMAKE_DEFINE_ALIASES.items():
            if name in self.data:
                value = self.data.pop(name)
                self.cmake_defines[cmake_define_name] = value

    def assign(self, data):
        # -- WORKS WITH: this-class or dict-like
        if isinstance(data, self.__class__):
            data = data.data

        the_data = deepcopy(CMAKE_CONFIG_DEFAULTS)
        the_data.update(data)
        self.data = the_data
        self.normalize_data()

    # -- DICT-LIKE API:
    def clear(self):
        self.data.clear()
        self.data.update(CMAKE_CONFIG_DEFAULTS)

    def get(self, name, default=None):
        define_name = self.CMAKE_DEFINE_ALIASES.get(name, None)
        if define_name:
            return self.cmake_defines.get(define_name, default)
        return self.data.get(name, default)
        # value = getattr(self, name, Unknown)
        # if value is Unknown:
        #     value = self.data.get(name, default)
        # return value

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def update(self, data, **kwargs):
        self.data.update(data, **kwargs)
        self.normalize_data()

    def copy(self):
        return self.__class__(data=deepcopy(self.data))

    def __len__(self):
        return len(self.data)

    def __contains__(self, param_name):
        define_name = self.CMAKE_DEFINE_ALIASES.get(param_name, None)
        if define_name:
            return define_name in self.cmake_defines
        return param_name in self.data

    def __getitem__(self, param_name):
        define_name = self.CMAKE_DEFINE_ALIASES.get(param_name, None)
        if define_name:
            # -- HINT: Avoid KeyError if cmake_define is not stored.
            return self.cmake_defines.get(define_name, None)
        return self.data[param_name]

    def __setitem__(self, param_name, value):
        define_name = self.CMAKE_DEFINE_ALIASES.get(param_name, None)
        if define_name:
            self.cmake_defines[define_name] = value
            return
        self.data[param_name] = value

    def __eq__(self, other):
        # -- HINT: Ignore self.name
        # if isinstance(other, dict):
        #     return self.data == other
        # return self.data == other.data
        return self.same_as(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def same_as(self, other, excluded=None):
        """Compare if this config is the same as the other."""
        # -- OPTIMIZATION: Only applicable w/o excluded parts.
        excluded = set(excluded or [])
        diff = set(self.data.keys()).symmetric_difference(other.keys())
        diff_without_excluded = diff.difference(excluded)
        if diff_without_excluded:
            return False

        # -- NORMAL CASE: Both configs have same keys (ignoring excluded)
        for name, value in self.data.items():
            if excluded and name in excluded:
                continue
            elif name == "cmake_defines":
                continue

            other_value = other.get(name)
            if value != other_value:
                return False

        # -- OTHERWISE: Same except in excludes.
        # HINT: Ignore ordering Compare without
        return unordered_dict_equals(self.cmake_defines, other["cmake_defines"])
        # return True

    @property
    def cmake_generator(self):
        return self.get("cmake_generator", None)

    @cmake_generator.setter
    def cmake_generator(self, value):
        self.data["cmake_generator"] = value

    @property
    def cmake_parallel(self):
        return self.get("cmake_parallel", 0)

    @cmake_parallel.setter
    def cmake_parallel(self, value):
        self.data["cmake_parallel"] = value

    # -- CMAKE-DEFINES:
    @property
    def cmake_toolchain(self):
        return self.cmake_defines.get("CMAKE_TOOLCHAIN_FILE", None)
        # OLD: return self.get("cmake_toolchain", None)

    @cmake_toolchain.setter
    def cmake_toolchain(self, value):
        self.cmake_defines["CMAKE_TOOLCHAIN_FILE"] = value
        # OLD: self.data["cmake_toolchain"] = value

    @property
    def cmake_build_type(self):
        return self.cmake_defines.get("CMAKE_BUILD_TYPE", None)
        # OLD: return self.get("cmake_build_type", None)

    @cmake_build_type.setter
    def cmake_build_type(self, value):
        self.cmake_defines["CMAKE_BUILD_TYPE"] = value
        # OLD: self.data["cmake_build_type"] = value

    @property
    def cmake_install_prefix(self):
        return self.cmake_defines.get("CMAKE_INSTALL_PREFIX", None)
        # OLD: return self.get("cmake_install_prefix", None)

    @cmake_install_prefix.setter
    def cmake_install_prefix(self, value):
        self.cmake_defines["CMAKE_INSTALL_PREFIX"] = value
        # OLD: self.data["cmake_install_prefix"] = value

    @property
    def cmake_defines(self):
        return self.data["cmake_defines"]

    @cmake_defines.setter
    def cmake_defines(self, value):
        if not isinstance(value, OrderedDict):
            value = OrderedDict(value)
        self.data["cmake_defines"] = value

    # -- CMAKE-COMMAND-ARGS:
    @property
    def cmake_init_args(self):
        return self.get("cmake_args", [])

    @cmake_init_args.setter
    def cmake_init_args(self, value):
        self.data["cmake_init_args"] = value or []

    @property
    def cmake_build_args(self):
        return self.get("cmake_build_args", [])

    @cmake_build_args.setter
    def cmake_build_args(self, value):
        self.data["cmake_build_args"] = value or []

    @property
    def cmake_test_args(self):
        return self.get("cmake_test_args", [])

    @cmake_test_args.setter
    def cmake_test_args(self, value):
        self.data["cmake_test_args"] = value or []

    # XXX-JE-CHECK-CAN-BE-REMOVED
    def cmake_defines_add(self, name, value=None):
        # OLD: self.cmake_defines.update([(name, value)])
        self.cmake_defines[name] = value

    # XXX-JE-CHECK-CAN-BE-REMOVED
    def cmake_defines_remove(self, name):
        if name in self.cmake_defines:
            self.cmake_defines.pop(name)

    def add_cmake_defines(self, defines):
        if isinstance(defines, OrderedDict):
            self.cmake_defines.update(defines)
        elif not isinstance(defines, (list, tuple)):
            raise ValueError("BAD-TYPE: %s (expected: OrderedDict, list, tuple" %
                             type(defines))

        for cmake_define in defines:
            if isinstance(cmake_define, str):
                cmake_define = CMakeDefine.parse(cmake_define)

            if isinstance(cmake_define, CMakeDefine):
                name = cmake_define.name
                value = cmake_define.value
            elif isinstance(cmake_define, tuple):
                assert len(cmake_define) == 2
                name, value = cmake_define
            else:
                raise ValueError("BAD-TYPE: %r (expected: string, tuple)")
            self.cmake_defines[name] = value


class CMakeProjectPersistConfig(CMakeProjectConfig, PersistentData):
    """Persistent data class for CMake project (build_dir) config data.
    This data represents one build-configuration of this project.
    """
    FILE_BASENAME = ".cmake_build.build_config.json"

    def __init__(self, filename=None, data=None, cmake_generator=None,
                 cmake_toolchain=None, **kwargs):
        # if not data:
        #     data = deepcopy(CMAKE_CONFIG_DEFAULTS)

        # -- SETUP/INIT: BASE-CLASSES
        CMakeProjectConfig.__init__(self, data=data, **kwargs)
        PersistentData.__init__(self, filename, data=self.data)
        if cmake_generator:
            self.cmake_generator = cmake_generator
        if cmake_toolchain:
            self.cmake_toolchain = cmake_toolchain

    def assign(self, data):
        # -- MAYBE-BETTER:
        # CMakeProjectConfig.assign(self, data)
        # return

        # XXX-OLD-IMPLEMENTATION:
        # -- WORKS WITH: this-class or dict-like
        the_data = data
        if isinstance(data, self.__class__):
            the_data = data.data

        # -- ENSURE: All parameters exists, at least with default values.
        # HINT: Needed if newer cmake-builds stumbles upon older persistent schema.
        # data = {
        #     "cmake_build_type": None,
        #     "cmake_defines": {},
        #     "cmake_generator": None,
        #     "cmake_install_prefix": None,
        #     "cmake_toolchain": None,
        # }
        data = deepcopy(CMAKE_CONFIG_DEFAULTS)
        data.update(the_data)
        self.data = data
        self.normalize_data()


class BuildConfig(CMakeProjectConfig):
    """Represent the configuration data related to a build-configuration.


    .. code-block:: YAML

        # -- FILE: cmake_build.yaml
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
        CMakeProjectConfig.__init__(self, data, **kwargs)
        self.name = name or self.DEFAULT_NAME
        self._cmake_build_type = self.cmake_build_type
        self.derive_cmake_build_type_if_unconfigured()

    def derive_cmake_build_type(self):
        """Derives CMAKE_BUILD_TYPE from build_config.name."""
        return map_build_config_to_cmake_build_type(self.name)

    def derive_cmake_build_type_and_assign(self, force=False):
        # pylint: disable=invalid-name
        """Derives CMAKE_BUILD_TYPE and assigns it,
        if the CMAKE_BUILD_TYPE is not configured yet.
        """
        if force or self.CMAKE_BUILD_TYPE_AUTO_DETECT:
            # -- NOT-CONFIGURED: cmake_build_type
            # HINT: Derive cmake_build_type from build_config.name
            self.cmake_build_type = self.derive_cmake_build_type()
        return self.cmake_build_type

    def derive_cmake_build_type_if_unconfigured(self):
        # pylint: disable=invalid-name
        """Derives CMAKE_BUILD_TYPE and assigns it,
        if the CMAKE_BUILD_TYPE is not configured yet.
        """
        not_configured = not self._cmake_build_type
        if not_configured:
            self.derive_cmake_build_type_and_assign()
        return self.cmake_build_type

    @property
    def cmake_build_type(self):
        return self.cmake_defines.get("CMAKE_BUILD_TYPE", None)

    @cmake_build_type.setter
    def cmake_build_type(self, value):
        self.cmake_defines["CMAKE_BUILD_TYPE"] = value
        self._cmake_build_type = value
