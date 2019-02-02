# -*- coding: UTF-8 -*-

import cmake_build.cmake_util
from cmake_build.cmake_util import *
import pytest


# ---------------------------------------------------------------------------
# TEST SUPPORT
# ---------------------------------------------------------------------------
class MockConfig(object):
    def __init__(self, data=None, **kwargs):
        data = data or {}
        data.update(**kwargs)
        for name, value in data.iteritems():
            setattr(self, name, value)

# ---------------------------------------------------------------------------
# TESTS FOR: map_build_config_to_cmake_build_type()
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("build_config, expected", [
    ("arm64_Debug", "Debug"),
    ("debug_arm64", "Debug"),
    ("Linux_x86_64_Release", "Release"),
    ("Linux_release_x86_64", "Release"),
])
def test_map_build_config_to_cmake_build_type(build_config, expected):
    cmake_build_type = map_build_config_to_cmake_build_type(build_config)
    assert cmake_build_type == expected


# ---------------------------------------------------------------------------
# TESTS FOR: make_build_dir_from_schema()
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name, build_dir_schema, expected", [
    ("hello", "build.{BUILD_CONFIG}", "build.hello"),
    ("foo",   "build/{BUILD_CONFIG}", "build/foo"),
    ("bar",   "build", "build"),
])
def test_make_build_dir_from_schema__with_config_build_dir_schema(name, build_dir_schema, expected):
    build_config_name = name
    config = MockConfig(build_dir_schema=build_dir_schema)
    build_dir = make_build_dir_from_schema(config, build_config_name)
    assert build_dir == expected


def test_make_build_dir_from_schema__without_config_build_dir_schema(monkeypatch):
    build_config_name = "hello"
    with monkeypatch.context() as m:
        m.setattr(cmake_build.cmake_util, "BUILD_DIR_SCHEMA", "__build.{BUILD_CONFIG}")
        expected = "__build.{0}".format(build_config_name)
        config = MockConfig(build_dir_schema=None)
        build_dir = make_build_dir_from_schema(config, build_config_name)
        assert build_dir == expected


# ---------------------------------------------------------------------------
# TESTS FOR: cmake_defines_add()
# ---------------------------------------------------------------------------
TEST_DEFINITIONS = [
    ("one", "ONE_VALUE"),
    ("two", "TWO_VALUE"),
    ("three", "THREE_VALUE"),
]


@pytest.mark.parametrize("define", [
    ("one", "ONE"),
    ("two", "TWO_VALUE"),
])
def test_cmake_defines_add__with_new_define_is_appended(define):
    definitions = []
    name, value = define
    cmake_defines_add(definitions, name, value)
    assert len(definitions) == 1
    assert definitions[-1] == define, "ENSURE: Appended (LAST-ITEM)"


@pytest.mark.parametrize("definitions, define", [
    (list(TEST_DEFINITIONS), ("one",  "ON")),
    (list(TEST_DEFINITIONS), ("two", "TWO_NEW_VALUE")),
    (list(TEST_DEFINITIONS), ("three", True)),
])
def test_cmake_defines_add__with_existing_define_is_replaced(definitions, define):
    initial_size = len(definitions)
    name, value = define
    cmake_defines_add(definitions, name, value)
    assert len(definitions) == initial_size
    assert define in definitions, "ENSURE: New define replaces existing"


def test_cmake_defines_add__with_value_none_has_value_on():
    # -- CASE 1: Call with value=None
    definitions = []
    expected_item = ("one", "ON")
    cmake_defines_add(definitions, "one", value=None)
    assert len(definitions) == 1
    assert expected_item in definitions, "ENSURE: Uses value=ON"


def test_cmake_defines_add__without_value_none_has_value_on():
    # -- CASE 2: Call without value
    definitions = []
    expected_item = ("one", "ON")
    cmake_defines_add(definitions, "one")
    assert len(definitions) == 1
    assert expected_item in definitions, "ENSURE: Uses value=ON"


# ---------------------------------------------------------------------------
# TESTS FOR: cmake_cmdline_generator_option()
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("generator, expected", [
    ("foo",            "-G foo"),
    ("Ninja",          "-G Ninja"),
])
def test_cmake_cmdline_generator_option__with_one_word_is_unquoted(generator, expected):
    text = cmake_cmdline_generator_option(generator)
    assert text.strip() == expected


@pytest.mark.parametrize("generator, expected", [
    ("two words", "-G 'two words'"),
    ("Unix Makefiles", "-G 'Unix Makefiles'"),
])
def test_cmake_cmdline_generator_option__with_two_words_are_quoted(generator, expected):
    text = cmake_cmdline_generator_option(generator)
    assert text.strip() == expected


@pytest.mark.parametrize("generator, expected", [
    ("ninja", "-G Ninja"),
    ("make",  "-G 'Unix Makefiles'"),
])
def test_cmake_cmdline_generator_option__with_alias(generator, expected):
    text = cmake_cmdline_generator_option(generator)
    assert text.strip() == expected
    assert generator in CMAKE_GENERATOR_ALIAS_MAP


def test_cmake_cmdline_generator_option__with_none_is_empty():
    text = cmake_cmdline_generator_option(None)
    assert text == ""


# ---------------------------------------------------------------------------
# TESTS FOR: cmake_cmdline_toolchain_option()
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("toolchain", [
    "cmake/toolchain/one.cmake"
])
def test_cmake_cmdline_toolchain_option__with_toolchain_uses_abspath(toolchain):
    expected = "-DCMAKE_TOOLCHAIN_FILE={0}".format(Path(toolchain).abspath())
    text = cmake_cmdline_toolchain_option(toolchain)
    assert text == expected


def test_cmake_cmdline_toolchain_option__without_toolchain_is_empty():
    text = cmake_cmdline_toolchain_option(None)
    assert text == ""


# ---------------------------------------------------------------------------
# TESTS FOR: cmake_normalize_defines()
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("expected, defines", [
    ([("one", "VALUE_1")],                      [("one", "VALUE_1")]),
    ([("one", "VALUE_1"), ("TWO", "value_2")],  [("one", "VALUE_1"), ("TWO", "value_2")]),
])
def test_cmake_normalize_defines__with_tuple(expected, defines):
    actual = cmake_normalize_defines(defines)
    assert actual == expected


@pytest.mark.parametrize("expected, defines", [
    ([("one", "VALUE_1")],               [dict(one="VALUE_1")]),
    ([("one", "VALUE_1"), ("TWO", "value_2")], [dict(one="VALUE_1"), {"TWO": "value_2"}]),
])
def test_cmake_normalize_defines__with_dict(expected, defines):
    actual = cmake_normalize_defines(defines)
    assert actual == expected


@pytest.mark.parametrize("expected, defines", [
    ([("one", "VALUE_1")],                  ["one=VALUE_1"]),
    ([("one", "VALUE_1"), ("TWO", None)],   ["one=VALUE_1", "TWO"]),
])
def test_cmake_normalize_defines__with_string(expected, defines):
    actual = cmake_normalize_defines(defines)
    assert actual == expected


# ---------------------------------------------------------------------------
# TESTS FOR: cmake_cmdline_defines_option()
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("expected, defines", [
    ("-Done=VALUE_1",               [("one", "VALUE_1")]),
    ("-Done=VALUE_1 -DTWO=value_2", [("one", "VALUE_1"), ("TWO", "value_2")]),
])
def test_cmake_cmdline_defines_option__with_defines(expected, defines):
    actual = cmake_cmdline_defines_option(defines)
    assert actual == expected


@pytest.mark.parametrize("expected, defines", [
    ("-Dfoo", [("foo", None)]),
])
def test_cmake_cmdline_defines_option__with_value_none(expected, defines):
    actual = cmake_cmdline_defines_option(defines)
    assert actual == expected


@pytest.mark.parametrize("expected, toolchain, defines", [
    ("-DCMAKE_TOOLCHAIN_FILE=$ABSPATH/t1.cmake -Done=VALUE_1", "t1.cmake", [("one", "VALUE_1")]),
])
def test_cmake_cmdline_defines_option__with_defines_and_toolchain(expected, toolchain, defines):
    actual = cmake_cmdline_defines_option(defines, toolchain=toolchain)
    normalized = actual.replace(Path(".").abspath(), "$ABSPATH").replace("\\", "/")
    assert normalized == expected


# ---------------------------------------------------------------------------
# TESTS FOR: cmake_cmdline()
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("generator", [
    "Ninja",
    "Unix Makefiles",
    "ninja",
    "make",
])
def test_cmake_cmdline__with_generator(generator):
    expected = cmake_cmdline_generator_option(generator).strip()
    actual = cmake_cmdline(generator=generator)
    assert actual == expected


@pytest.mark.parametrize("toolchain", [
    "cmake/toolchain/t1.cmake",
])
def test_cmake_cmdline__with_toolchain(toolchain):
    expected = cmake_cmdline_toolchain_option(toolchain)
    actual = cmake_cmdline(toolchain=toolchain)
    assert actual == expected


@pytest.mark.parametrize("defines", [
    [("one", "VALUE_1")],
    [("one", "VALUE_1"), ("two", "value_2")],
])
def test_cmake_cmdline__with_defines(defines):
    expected = cmake_cmdline_defines_option(defines)
    actual = cmake_cmdline(defines=defines)
    assert actual == expected


@pytest.mark.parametrize("args", [
    "",
    "--build .",
    "--warn-uninitialized",
])
def test_cmake_cmdline__with_args_as_string(args):
    expected = args.strip()
    actual = cmake_cmdline(args).strip()
    assert actual == expected


@pytest.mark.parametrize("args", [
    ["--warn-uninitialized"],
    ["--warn-uninitialized", "--warn-unused-var"],
])
def test_cmake_cmdline__with_args_as_list(args):
    expected = " ".join(args)
    actual = cmake_cmdline(args=args).strip()
    assert actual == expected


@pytest.mark.parametrize("args, defines", [
    ("--build .", [("one", "VALUE_1")]),
    ("--warn-uninitialized", [("one", "VALUE_1"), ("two", "VALUE_2")]),
])
def test_cmake_cmdline__with_args_and_defines(args, defines):
    defines_option = cmake_cmdline_defines_option(defines) + " "
    expected = "{0} {1}".format(defines_option, args).replace("  ", " ")
    actual = cmake_cmdline(args, defines=defines)
    assert actual == expected


def test_cmake_cmdline__with_all():
    return NotImplemented
