# -*- coding: UTF-8 -*-
"""
Behave fixtures for cmake-build.
"""

from __future__ import absolute_import
import os
from behave.fixture import fixture, fixture_call_params


# -----------------------------------------------------------------------------
# CONSTANTS:
# -----------------------------------------------------------------------------
YES_NO_MAPPING = {True: "yes", False: "no"}
EXCLUDED_ENVIRONMENT_VARIABLES = ["CMAKE_BUILD_INHERIT_CONFIG_FILE"]


# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS:
# -----------------------------------------------------------------------------
def cleanup_environment(pattern=None, excluded=None, environment=None):
    """Remove any CMAKE-BUILD environment variables.

    :param pattern: To select environment variables to cleanup.
    :param excluded: List of environemt variable names that are excluded.
    :param environment:  Use other dict to cleanup (default: os.environ)
    """
    environ = environment or os.environ
    excluded = excluded or EXCLUDED_ENVIRONMENT_VARIABLES
    for name in list(environ.keys()):
        if name in excluded:
            continue
        elif name.startswith("CMAKE_BUILD_"):
            del environ[name]
    return environ


def restore_environment(environment_data):
    os.environ = environment_data


# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------
# @fixture.cmake_build.cleanup_environment
@fixture
def fixture_cleanup_environment(ctx, **kwargs):
    """Behave fixture (function) to remove any "CMAKE_BUILD_*" environment
    variables from the environment.
    The cleanup is performed after the entity is executed.

    :param ctx: Context object to use
    """
    ctx.add_cleanup(cleanup_environment)


@fixture
def fixture_ensure_clean_environment(ctx, **kwargs):
    """Behave fixture (function) to remove any "CMAKE_BUILD_*" environment
    variables from the environment.
    The cleanup is performed before (and after) the entity is executed.

    :param ctx: Context object to use
    """
    # -- MAYBE:
    # initial_environment = os.environ.copy()
    # cleanup_environment()
    # ctx.add_cleanup(restore_environment, initial_environment)
    cleanup_environment()
    ctx.add_cleanup(cleanup_environment)


@fixture
def cmake_build_use_inherit_config_file(ctx, value=None):
    """Setup cmake-build to inherit/not-inherit the config-file
    from a parent directory (or above).

    :param ctx: Context object to use
    :param value: Inherit enabled or not (default: true; as bool/string/none)
    """
    ENV_VARIABLE_NAME = "CMAKE_BUILD_INHERIT_CONFIG_FILE"
    if isinstance(value, bool):
        value = YES_NO_MAPPING[value]

    initial_value = os.environ.get(ENV_VARIABLE_NAME)
    if value is None:
        # -- USE DEFAULT (without environment-variable = ENABLED)
        if initial_value is not None:
            del os.environ[ENV_VARIABLE_NAME]
    else:
        os.environ[ENV_VARIABLE_NAME] = value
    yield
    # -- CLEANUP AND RESTORE:
    if initial_value:
        os.environ[ENV_VARIABLE_NAME] = initial_value
    elif value and ENV_VARIABLE_NAME in os.environ:
        del os.environ[ENV_VARIABLE_NAME]


# @fixture
# def fixture_cmake_build_use_inherit_config_file(ctx, **kwargs):
#     return use_fixture(cmake_build_use_inherit_config_file, ctx)
#
# @fixture
# def fixture_cmake_build_use_inherit_config_file_enabled(ctx, **kwargs):
#     return use_fixture(cmake_build_use_inherit_config_file, ctx, value=True)
#
# @fixture
# def fixture_cmake_build_use_inherit_config_file_disabled(ctx, **kwargs):
#     return use_fixture(cmake_build_use_inherit_config_file, ctx, value=False)
#
# -----------------------------------------------------------------------------
# FIXTURE REGISTRY: Maps fixture-tag to fixture-func
# -----------------------------------------------------------------------------
fixture_registry = {
    "fixture.cmake_build.cleanup_environment": fixture_cleanup_environment,
    "fixture.cmake_build.ensure_clean_environment": fixture_ensure_clean_environment,
    "fixture.cmake_build.inherits_config_file": fixture_call_params(cmake_build_use_inherit_config_file, value=None),
    "fixture.cmake_build.inherit_config_file.enabled": fixture_call_params(cmake_build_use_inherit_config_file, value=True),
    "fixture.cmake_build.inherit_config_file.disabled": fixture_call_params(cmake_build_use_inherit_config_file, value=False),
    # -- ALIASES with SYNTACTIC SUGAR:
    "fixture.cmake_build.inherit_config_file=yes": fixture_call_params(cmake_build_use_inherit_config_file, value=True),
    "fixture.cmake_build.inherit_config_file=no": fixture_call_params(cmake_build_use_inherit_config_file, value=False),
}
