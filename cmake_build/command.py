# -*- coding: UTF-8 -*-
# WIP
# pylint: disable=no-value-for-parameter, unused-argument, unused-import
"""
Provides the command tool for command-line processing.

.. code-block::sh

    cmake-build --project=/foo/bar
    cmake-build --build-config=xxx_debug
    cmake-build -f cmake-build.other.yaml
    cmake-build --target=init
"""

from __future__ import absolute_import
import click
from path import Path
from .config import CMakeBuildConfig, CMakeBuildConfigValidator, CMAKE_BUILD_TARGETS
from .tasks import CMakeBuildRunner
from .version import VERSION


def cmake_build_run(config):
    validator = CMakeBuildConfigValidator(config)
    if not validator.check():
        click.echo(validator.error_message)
        return 100

    command_runner = CMakeBuildRunner(config)
    return command_runner.execute_target()


@click.command()
@click.option("-f", "--filename", type=click.Path(),
              default="cmake-build.config.yaml",
              help="cmake-build configuration file to use.")
@click.option("-b", "--build-config", default="default",
              help="Build configuration to use (by name).")
@click.option("-p", "--project", default="all", type=click.Path(file_okay=False),
              help="Select cmake project(s) to build (default: all).")
@click.option("-t", "--target",
              type=click.Choice(CMAKE_BUILD_TARGETS), default="build",
              help="CMake target to use (default: build).")
@click.version_option(VERSION)
@click.argument("args", required=False)     # MAYBE: multiple=True)
@click.pass_context
def cmake_build(ctx, filename, build_config, project, target, args=None):
    """cmake-build is a thin wrapper around CMake.
    It automatically initializes CMake projects by using the
    provided data in a configuration file.
    """
    # return cmake_build(args=args)
    def load_config(filename, **kwargs):
        return NotImplemented

    # -- STEPS:
    try:
        config = load_config(filename,
                             build_config=build_config,
                             project=project,
                             target=target)
        if config:
            result = cmake_build_run(config)
            verdict = "SUCCESS"
            if result != 0:
                verdict = "FAILED"
            click.echo("CMAKE-BUILD: {verdict}".format(verdict=verdict))
            ctx.exit(result)
        else:
            click.echo("CMAKE-BUILD: Missing config-file={0}".format(filename))
            ctx.exit(1)
    except KeyboardInterrupt:
        click.echo("ABORTED-BY-USER.")
        ctx.exit(3)
    except Exception as e:  # pylint: disable=broad-except
        click.echo("ERROR, CAUGHT EXCEPTION: {0}:{1}".format(
            e.__class__.__name__, e))
        ctx.exit(2)
    ctx.exit(0)

if __name__ == "__main__":
    cmake_build()
