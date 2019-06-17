# -*- coding: UTF-8 -*-
# pylint: disable=invalid-name, line-too-long, no-self-use, bad-whitespace
"""
Unit tests for :mod:`cmake_build.config`.
"""

from collections import OrderedDict
from copy import deepcopy
import pytest
from path import Path
from cmake_build.config import CMAKE_CONFIG_DEFAULTS, \
    CMakeProjectConfig, CMakeProjectPersistConfig, BuildConfig


# ---------------------------------------------------------------------------
# TESTS FOR: CMakeProjectConfig
# ---------------------------------------------------------------------------
# -- SUPPORT EQUAL-TO COMPARISON:
CMAKE_CONFIG_DEFAULTS.update(cmake_defines=OrderedDict())


# ---------------------------------------------------------------------------
# TESTS FOR: CMakeProjectConfig
# ---------------------------------------------------------------------------
class TestCMakeProjectConfig(object):

    def test_ctor__without_data_contains_default_values(self):
        project_data = CMakeProjectConfig()
        expected = CMAKE_CONFIG_DEFAULTS
        assert project_data.data
        assert len(project_data.data) == len(CMAKE_CONFIG_DEFAULTS)
        assert project_data.data == expected
        assert "cmake_generator" in project_data
        assert "cmake_parallel" in project_data
        assert "cmake_defines" in project_data
        assert "cmake_init_args" in project_data
        assert "cmake_build_args" in project_data
        # assert "cmake_build_type" in project_data
        # assert "cmake_toolchain" in project_data

    def test_ctor__kwargs_can_override_data(self):
        data = dict(one=1)
        kwargs = dict(one=2)
        project_data = CMakeProjectConfig(data.copy(), **kwargs)
        # assert project_data.data != data
        assert project_data.data["one"] == kwargs["one"]
        assert project_data.data["one"] != data["one"]

    def test_ctor__kwargs_can_extend_data(self):
        data = dict(one=1)
        kwargs = dict(two=2)
        project_data = CMakeProjectConfig(data.copy(), **kwargs)
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
        project_data1 = CMakeProjectConfig(data)
        project_data2 = CMakeProjectConfig(data=data.copy())
        assert project_data1 == project_data2
        assert project_data1.data is not project_data2.data

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(),      dict(one=1),  "different-size"),
        (dict(one=1), dict(one=2), "same-size/keys: different-values"),
        (dict(one=1, two=2), dict(one=1, two=42), "one value differs"),
        (dict(one=1, two=2), dict(one=1, three=3), "one key/item differs"),
    ])
    def test_equals__with_other_data(self, data1, data2, case):
        project_data1 = CMakeProjectConfig(data1)
        project_data2 = CMakeProjectConfig(data2)
        assert project_data1 != project_data2, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=dict(k1=[1, 2, 3])), dict(one=dict(k1=[1, 3, 2])), "deep different-values"),
    ])
    def test_equals__with_other_data_and_deep_diff(self, data1, data2, case):
        project_data1 = CMakeProjectConfig(data1)
        project_data2 = CMakeProjectConfig(data2)
        assert project_data1 != project_data2, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=1), dict(one=1), "same_data"),
    ])
    def test_equals__can_compare_with_same_dict(self, data1, data2, case):
        project_data1 = CMakeProjectConfig(data1)
        data2.update(CMAKE_CONFIG_DEFAULTS)
        assert project_data1 == data2, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=1), dict(one=12), "different-values"),
    ])
    def test_equals__can_compare_with_other_dict(self, data1, data2, case):
        project_data1 = CMakeProjectConfig(data1)
        data2.update(CMAKE_CONFIG_DEFAULTS)
        assert project_data1 != data2, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=1), dict(one=1), "same_data"),
        (dict(one=1, two=2), dict(one=1, two=2), "same_data"),
    ])
    def test_same_as__returns_true_with_same_data(self, data1, data2, case):
        config1 = CMakeProjectConfig(data1)
        config2 = CMakeProjectConfig(data2)
        outcome = config1.same_as(config2)
        assert outcome is True, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, case", [
        (dict(one=1), dict(one=1, two=2), "different length"),
        (dict(one=1), dict(one=1, three=3), "additional parts in data2"),
        (dict(one=1, two=2), dict(one=1), "additional parts in data1"),
        (dict(one=1, two=2), dict(one=1, three=3), "additional parts in each"),
        (dict(one=1, two=2), dict(one=1, two=20), "some values differ"),
    ])
    def test_same_as__returns_false_with_other_data(self, data1, data2, case):
        config1 = CMakeProjectConfig(data1)
        config2 = CMakeProjectConfig(data2)
        outcome = config1.same_as(config2)
        assert outcome is False, "CASE: %s" % case

    @pytest.mark.parametrize("data1, data2, excluded", [
        # -- CASE: data-view is same if excluded parts are ignored
        (dict(one=1), dict(one=1, two=2), ["two"]),
        (dict(one=1, two=2), dict(one=1, three=3), ["two", "three"]),
        (dict(one=1, two=2), dict(one=1, two=20), ["two"]),
    ])
    def test_same_as__returns_true_with_excluded(self, data1, data2, excluded):
        config1 = CMakeProjectConfig(data1)
        config2 = CMakeProjectConfig(data2)
        outcome1 = config1.same_as(config2, excluded=excluded)
        outcome2 = config2.same_as(config1, excluded=excluded)
        assert outcome1 is True
        assert outcome1 == outcome2

    @pytest.mark.parametrize("data1, data2, excluded", [
        # -- CASE: data-view is differs even if excluded parts are ignored
        (dict(one=1), dict(one=10, two=2), ["two"]), # CASE: value(s) differ
        (dict(one=1), dict(ONE=1, two=2), ["two"]),  # CASE: key(s) differ
        (dict(one=1, two=2), dict(one=10, three=3), ["two", "three"]),
        (dict(one=1, two=2), dict(one=10, two=20), ["two"]),
    ])
    def test_same_as__returns_false_with_excluded(self, data1, data2, excluded):
        config1 = CMakeProjectConfig(data1)
        config2 = CMakeProjectConfig(data2)
        outcome1 = config1.same_as(config2, excluded=excluded)
        outcome2 = config2.same_as(config1, excluded=excluded)
        assert outcome1 is False
        assert outcome1 == outcome2

    @pytest.mark.parametrize("expected, data1, data2", [
        (True,  dict(one=1, two=2), dict(one=1, two=2)), # CASE: same
        (False, dict(one=1, two=2), dict(one=1, two=3)), # CASE: not-same
    ])
    def test_same_as__outcome_is_independent_of_ordering(self, expected, data1, data2):
        config1 = CMakeProjectConfig(data1)
        config2 = CMakeProjectConfig(data2)
        outcome1 = config1.same_as(config2)
        outcome2 = config2.same_as(config1)
        assert outcome1 == outcome2
        assert expected == outcome1


class TestCMakeProjectConfig4CMakeDefineProtocol(object):
    """Verifies the CMakeDefine protocol."""
    CMAKE_DEFINE_ALIASES = [
        "cmake_toolchain", "cmake_build_type", "cmake_install_prefix"
    ]

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_get_attribute__returns_none_with_empty_config(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        config = CMakeProjectConfig()
        value = getattr(config, cmake_define_alias)
        assert value is None
        assert config.cmake_defines.get(cmake_define_name) is None
        assert cmake_define_alias not in config.data

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_get_attribute__returns_value_with_non_empty_config(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        expected_value = "value_1:{0}".format(cmake_define_alias.upper())
        data = dict()
        data[cmake_define_alias] = expected_value
        config = CMakeProjectConfig(data)
        value = getattr(config, cmake_define_alias)
        assert value == expected_value
        assert config.cmake_defines[cmake_define_name] == expected_value
        assert cmake_define_alias not in config.data
        assert cmake_define_name in config.cmake_defines

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_set_attribute__stores_value_in_cmake_defines(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        value = "value_2:{0}".format(cmake_define_alias.upper())
        config = CMakeProjectConfig()
        setattr(config, cmake_define_alias, value)
        stored_value = getattr(config, cmake_define_alias)
        assert config.cmake_defines[cmake_define_name] == value
        assert cmake_define_alias not in config.data
        assert value == stored_value

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_getitem__returns_none_with_empty_config(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        config = CMakeProjectConfig()
        value = config[cmake_define_alias]
        assert value is None
        assert cmake_define_name not in config.cmake_defines
        assert cmake_define_alias not in config.data

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_getitem__returns_value_with_non_empty_config(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        expected_value = "value:{0}".format(cmake_define_alias.upper())
        data = dict()
        data[cmake_define_alias] = expected_value
        config = CMakeProjectConfig(data)
        value = config[cmake_define_alias]
        assert value == expected_value
        assert config.cmake_defines[cmake_define_name] == expected_value
        assert cmake_define_alias not in config.data
        assert cmake_define_name in config.cmake_defines

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_setitem__stores_value_in_cmake_defines(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        value = "value:{0}".format(cmake_define_alias.upper())
        config = CMakeProjectConfig()
        config[cmake_define_alias] = value
        stored_value = config[cmake_define_alias]
        assert config.cmake_defines[cmake_define_name] == value
        assert cmake_define_alias not in config.data
        assert value == stored_value

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_get__returns_none_with_empty_config(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        config = CMakeProjectConfig()
        value = config.get(cmake_define_alias)
        assert value is None
        assert config.cmake_defines.get(cmake_define_name) is None
        assert cmake_define_alias not in config.data
        assert cmake_define_name not in config.cmake_defines

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_get__returns_value_with_non_empty_config(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        expected_value = "value_1:{0}".format(cmake_define_alias.upper())
        data = dict()
        data[cmake_define_alias] = expected_value
        config = CMakeProjectConfig(data)
        value = config.get(cmake_define_alias)
        assert value == expected_value
        assert config.cmake_defines[cmake_define_name] == expected_value
        assert cmake_define_alias not in config.data
        assert cmake_define_name in config.cmake_defines

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_contains__returns_true_if_stored_in_cmake_defines(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        config = CMakeProjectConfig()
        config.cmake_defines[cmake_define_name] = "__ANY_VALUE"
        outcome = cmake_define_alias in config
        assert outcome is True
        # -- SANITY-CHECKS:
        assert cmake_define_alias not in config.data
        assert cmake_define_name in config.cmake_defines

    @pytest.mark.parametrize("cmake_define_alias", CMAKE_DEFINE_ALIASES)
    def test_contains__returns_false_if_not_stored_in_cmake_defines(self, cmake_define_alias):
        cmake_define_name = CMakeProjectConfig.CMAKE_DEFINE_ALIASES[cmake_define_alias]
        config = CMakeProjectConfig()
        outcome = cmake_define_alias in config
        assert outcome is False
        # -- SANITY-CHECKS:
        assert cmake_define_alias not in config.data
        assert cmake_define_name not in config.cmake_defines

# ---------------------------------------------------------------------------
# TESTS FOR: CMakeProjectPersistConfig
# ---------------------------------------------------------------------------
def make_config(cmake_toolchain=None):
    cmake_defines = OrderedDict()
    if cmake_toolchain:
        cmake_defines["CMAKE_TOOLCHAIN_FILE"] = cmake_toolchain

    data = dict(cmake_defines=cmake_defines)
    return data


class TestCMakeProjectPersistConfig(object):

    def test_ctor__without_data_contains_defaults(self):
        project_data = CMakeProjectPersistConfig()
        assert project_data.data
        assert project_data == CMAKE_CONFIG_DEFAULTS

    def test_ctor__kwargs_can_override_data(self):
        data = dict(one="ORIGINAL")
        project_data = CMakeProjectPersistConfig(data=data, one="OTHER")
        assert project_data["one"] == "OTHER"

    def test_ctor__cmake_toolchain_can_override_data(self):
        # XXX data = dict(cmake_defines=dict(CMAKE_TOOLCHAIN_FILE="ORIGINAL_TOOLCHAIN"))
        data = make_config(cmake_toolchain="TOOLCHAIN_1")
        project_data = CMakeProjectPersistConfig(data=data,
                                                 cmake_toolchain="OTHER_TOOLCHAIN")
        assert project_data.cmake_toolchain == "OTHER_TOOLCHAIN"
        # OLD: assert project_data["cmake_toolchain"] == "OTHER_TOOLCHAIN"

    def test_ctor__cmake_generator_can_override_data(self):
        data = dict(cmake_generator="ORIGINAL")
        project_data = CMakeProjectPersistConfig(data=data,
                                                 cmake_generator="OTHER")
        assert project_data["cmake_generator"] == "OTHER"
        assert project_data.cmake_generator == "OTHER"

    def test_load__with_non_existent_file_provides_defaults(self, tmp_path):
        filename = tmp_path / CMakeProjectPersistConfig.FILE_BASENAME
        assert not Path(filename).exists()
        project_data = CMakeProjectPersistConfig.load(filename)
        assert project_data == CMAKE_CONFIG_DEFAULTS

    def test_load__with_existent_file(self, tmp_path):
        filename = Path(str(tmp_path / CMakeProjectPersistConfig.FILE_BASENAME))
        filename.remove_p()
        assert not filename.exists()

        data = {
            "cmake_generator": "ninja",
            "cmake_toolchain": "cmake/toolchain/t1.cmake",
            "cmake_build_type": "Release",
        }
        project_data1 = CMakeProjectPersistConfig(filename, data=data)
        project_data1.save()
        assert filename.exists()

        project_data2 = CMakeProjectPersistConfig.load(filename)
        expected = deepcopy(CMAKE_CONFIG_DEFAULTS)
        expected.update(dict(
            cmake_generator="ninja",
            cmake_defines=OrderedDict([
                ("CMAKE_TOOLCHAIN_FILE", "cmake/toolchain/t1.cmake"),
                ("CMAKE_BUILD_TYPE", "Release"),
            ])
        ))
        assert project_data2 == expected
        assert project_data2 == project_data1
        assert project_data2 != CMAKE_CONFIG_DEFAULTS

    def test_load__raises_error_for_bad_file_contents(self, tmp_path):
        bad_contents_filename = Path(str(tmp_path / "BAD_CONTENTS.json"))
        bad_contents_filename.remove_p()
        assert not bad_contents_filename.exists()

        # -- PROBLEM: MISSING-COMMA after "one" value => JSON ParseError
        bad_contents = """
            {
                "one": 1
                "two": 2
            }
            """
        with open(bad_contents_filename, "w") as f:
            f.write(bad_contents)
        assert bad_contents_filename.exists()

        with pytest.raises(ValueError):
            CMakeProjectPersistConfig.load(bad_contents_filename)



# ---------------------------------------------------------------------------
# TESTS FOR: BuildConfig
# ---------------------------------------------------------------------------
class TestBuildConfig(TestCMakeProjectConfig):
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
        config = BuildConfig(cmake_generator="foo")
        assert config.cmake_generator == "foo"
        assert config.get("cmake_generator") == "foo"
        assert config["cmake_generator"] == "foo"
        assert config.data.get("cmake_generator") == "foo"


    def test_cmake_generator__without_generator(self):
        config = BuildConfig()
        cmake_generator1 = config.get("cmake_generator", None)
        cmake_generator2 = config["cmake_generator"]
        assert config.cmake_generator is None
        assert cmake_generator1 is None
        assert cmake_generator2 is None

    def test_cmake_toolchain__with_toolchain(self):
        config = BuildConfig(cmake_toolchain="cmake/toolchain_1.cmake")
        assert config.cmake_toolchain == "cmake/toolchain_1.cmake"
        assert config.get("cmake_toolchain") == "cmake/toolchain_1.cmake"
        assert config["cmake_toolchain"] == "cmake/toolchain_1.cmake"
        # OLD assert config.data.get("cmake_toolchain") == "cmake/toolchain_1.cmake"

    def test_cmake_toolchain__without_toolchain(self):
        config = BuildConfig()
        cmake_toolchain1 = config.get("cmake_toolchain", None)
        cmake_toolchain2 = config["cmake_toolchain"]
        assert config.cmake_toolchain is None
        assert cmake_toolchain1 is None
        assert cmake_toolchain2 is None

    def test_cmake_defines__with_one_item(self):
        config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        expected = [("one", "VALUE_1"), ("CMAKE_BUILD_TYPE", None)]
        assert isinstance(config.cmake_defines, OrderedDict)
        assert list(config.cmake_defines.items()) == expected
        assert list(config.get("cmake_defines").items()) == expected
        assert list(config["cmake_defines"].items()) == expected
        assert list(config.data.get("cmake_defines").items()) == expected

    def test_cmake_defines__without_explicit_init(self):
        config = BuildConfig("debug")
        expected = [("CMAKE_BUILD_TYPE", "Debug")]
        assert list(config.cmake_defines.items()) == expected
        assert list(config["cmake_defines"].items()) == expected

    def test_cmake_defines__set(self):
        config = BuildConfig()
        definitions = [("one", "VALUE_1"), ("two", "VALUE_2")]
        config.cmake_defines = definitions  # XXX-BAD
        # XXX expected = [("CMAKE_BUILD_TYPE", None)] + definitions
        assert list(config.cmake_defines.items()) == definitions
        assert list(config["cmake_defines"].items()) == definitions

    # XXX-CANDIDATE-FOR-REMOVAL
    def test_cmake_defines_add__with_new_item_appends(self):
        config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        config.cmake_defines_add("NEW", "NEW_VALUE")
        expected = [
            ("one", "VALUE_1"),
            ("CMAKE_BUILD_TYPE", None),
            ("NEW", "NEW_VALUE"),
        ]
        assert list(config.cmake_defines.items()) == expected
        assert list(config["cmake_defines"].items()) == expected

    def test_cmake_defines_add__with_existing_item_overrides(self):
        config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        config.cmake_defines_add("one", "NEW_VALUE")
        expected = [("one", "NEW_VALUE"), ("CMAKE_BUILD_TYPE", None)]
        assert list(config.cmake_defines.items()) == expected
        assert list(config["cmake_defines"].items()) == expected

    def test_cmake_defines_remove__with_unknown_item(self):
        config = BuildConfig(cmake_defines=[("one", "VALUE_1")])
        config.cmake_defines_remove("UNKNOWN")
        expected = [("one", "VALUE_1"), ("CMAKE_BUILD_TYPE", None)]
        assert list(config.cmake_defines.items()) == expected
        assert list(config["cmake_defines"].items()) == expected

    def test_cmake_defines_add__with_existing_item_removes_it(self):
        definitions = [("one", "VALUE_1"), ("two", "VALUE_2")]
        config = BuildConfig(cmake_defines=definitions)
        config.cmake_defines_remove("two")
        expected = [("one", "VALUE_1"), ("CMAKE_BUILD_TYPE", None)]
        assert list(config.cmake_defines.items()) == expected
        assert list(config["cmake_defines"].items()) == expected


class TestBuildConfig_DeriveCMakeBuildType(object):
    """Unittests for :class:`BuildConfig` related how the
    cmake_build_type / CMAKE_BUILD_TYPE information is derived.
    """
    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type(self, build_config_name, expected):
        config = BuildConfig(build_config_name)
        cmake_build_type = config.derive_cmake_build_type()
        assert config.name == build_config_name
        assert cmake_build_type == expected

    def test_derive_cmake_build_type__returns_none_without_name(self):
        config = BuildConfig()
        cmake_build_type = config.derive_cmake_build_type()
        assert config.name == "default"
        assert cmake_build_type is None

    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type_if_unconfigured(self, build_config_name, expected):
        config = BuildConfig(build_config_name)
        config.cmake_build_type = None    # -- DISABLED: default-init.
        assert config.name == build_config_name
        assert config.cmake_build_type is None, "ENSURE: No assignment"

        cmake_build_type = config.derive_cmake_build_type_if_unconfigured()
        assert cmake_build_type == expected
        assert config.cmake_build_type == expected

    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type_if_unconfigured__with_initial_value(self, build_config_name, expected):
        config = BuildConfig(build_config_name, cmake_build_type="INITIAL")
        assert config.name == build_config_name
        assert config.cmake_build_type == "INITIAL"

        config.derive_cmake_build_type_if_unconfigured()
        derived_build_type = config.derive_cmake_build_type()
        assert config.cmake_build_type == "INITIAL", "ENSURE: INITIAL value is preserved."
        assert derived_build_type == expected
        assert derived_build_type != "INITIAL"

    @pytest.mark.parametrize("build_config_name, expected", [
        ("arm64_Debug", "Debug"),
        ("debug_arm64", "Debug"),
        ("Linux_x86_64_Release", "Release"),
        ("Linux_release_x86_64", "Release"),
    ])
    def test_derive_cmake_build_type_and_assign(self, build_config_name, expected):
        config = BuildConfig(build_config_name, cmake_build_type="INITIAL")
        assert config.name == build_config_name
        assert config.cmake_build_type == "INITIAL"

        cmake_build_type = config.derive_cmake_build_type_and_assign()
        assert cmake_build_type == expected
        assert config.cmake_build_type == expected
