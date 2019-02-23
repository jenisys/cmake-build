# -*- coding: UTF-8 -*-
"""
Behave fixtures for cmake-build.
"""

from __future__ import absolute_import
import os
from behave.fixture import fixture


# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS:
# -----------------------------------------------------------------------------
def cleanup_environment(pattern=None):
    """Remove any CMAKE-BUILD environment variables."""
    for name in list(os.environ.keys()):
        if name.startswith("CMAKE_BUILD_"):
            del os.environ[name]


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
    cleanup_environment()
    ctx.add_cleanup(cleanup_environment)


# -----------------------------------------------------------------------------
# FIXTURE REGISTRY: Maps fixture-tag to fixture-func
# -----------------------------------------------------------------------------
fixture_registry = {
    "fixture.cmake_build.cleanup_environment": fixture_cleanup_environment,
    "fixture.cmake_build.ensure_clean_environment": fixture_ensure_clean_environment,
}
