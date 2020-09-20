# -*- coding: UTF-8 -*-

from behave.tag_matcher import ActiveTagMatcher, setup_active_tag_values
from behave.fixture import use_fixture_by_tag
from behave4cmake_build.fixtures import fixture_registry as cmake_build_fixture_registry
from cmake_build.host_platform import cmake_system, cmake_machine
import os.path
import sys
import six


HERE = os.path.dirname(__file__)
TOPDIR = os.path.join(HERE, "..")
TOPDIR = os.path.abspath(TOPDIR)


# -- MATCHES ANY TAGS: @use.with_{category}={value}
# NOTE: active_tag_value_provider provides category values for active tags.
python_version = "%s.%s" % sys.version_info[:2]
active_tag_value_provider = {
    "python2": str(six.PY2).lower(),
    "python3": str(six.PY3).lower(),
    "python.version": python_version,
    # # -- python.implementation: cpython, pypy, jython, ironpython
    # "python.implementation": platform.python_implementation().lower(),
    # "pypy":    str("__pypy__" in sys.modules).lower(),
    "cmake_system":   cmake_system(),
    "cmake_cpu":      cmake_machine()
}
active_tag_matcher = ActiveTagMatcher(active_tag_value_provider)


# -----------------------------------------------------------------------------
# FIXTURE REGISTRY:
# -----------------------------------------------------------------------------
fixture_registry = {}
fixture_registry.update(cmake_build_fixture_registry)


# -----------------------------------------------------------------------------
# HOOKS:
# -----------------------------------------------------------------------------
def before_all(context):
    # -- SETUP ACTIVE-TAG MATCHER (with userdata):
    # USE: behave -D browser=safari ...
    setup_active_tag_values(active_tag_value_provider, context.config.userdata)
    setup_python_path()
    setup_command_shell_processors4cmake_build()
    cleanup_environment_variables()


def before_feature(context, feature):
    if active_tag_matcher.should_exclude_with(feature.tags):
        feature.skip(reason=active_tag_matcher.exclude_reason)


def before_scenario(context, scenario):
    if active_tag_matcher.should_exclude_with(scenario.effective_tags):
        scenario.skip(reason=active_tag_matcher.exclude_reason)


def before_tag(context, tag):
    if tag.startswith("fixture."):
        return use_fixture_by_tag(tag, context, fixture_registry)


# -----------------------------------------------------------------------------
# SPECIFIC FUNCTIONALITY:
# -----------------------------------------------------------------------------
def setup_python_path():
    # -- NEEDED-FOR: formatter.user_defined.feature
    # PYTHONPATH = os.environ.get("PYTHONPATH", "")
    # PYPATH_PREFIX = os.pathsep.join([TOPDIR, os.path.join(TOPDIR, "/lib/python")])
    # os.environ["PYTHONPATH"] = PYPATH_PREFIX + os.pathsep + PYTHONPATH
    topdir_extra_libdir = os.path.join(TOPDIR, "/lib/python")
    sys.path = [".", TOPDIR, topdir_extra_libdir] + sys.path


def setup_command_shell_processors4cmake_build():
    from behave4cmd0.command_shell import Command
    from behave4cmd0.command_shell_proc import BehaveWinCommandOutputProcessor, ExceptionWithPathNormalizer
    class CMakeBuildWinCommandOutputProcessor(BehaveWinCommandOutputProcessor):
        line_processors = BehaveWinCommandOutputProcessor.line_processors + [
            ExceptionWithPathNormalizer("CMAKE-INIT:  '(?P<path>.*)'", "CMAKE-INIT:  "),
        ]
    Command.POSTPROCESSOR_MAP["cmake-build"] = []
    for processor_class in [CMakeBuildWinCommandOutputProcessor]:
        if processor_class.enabled:
            processor = processor_class()
            Command.POSTPROCESSOR_MAP["cmake-build"].append(processor)

def cleanup_environment_variables():
    """Ensure that a clean process/shell environment exists
    without environment variables that cause side effects during tests:

    * CMAKE_BUILD_CONFIG
    * "CMAKE_*"
    """
    CLEANUP_VARIABLE_NAMES = ["CMAKE_BUILD_CONFIG"]
    for name in os.environ.keys():
        if name.startswith("CMAKE_") or (name in CLEANUP_VARIABLE_NAMES):
            print("REMOVE ENVIRONMENT-VARIABLE: {0}={1}".format(name, os.environ[name]))
            os.environ.pop(name)
