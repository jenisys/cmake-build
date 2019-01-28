# -*- coding: UTF-8 -*-
# pylint: disable=wrong-import-position, wrong-import-order
"""
Invoke build script.
Show all tasks with::

    invoke -l

.. seealso::

    * http://pyinvoke.org
    * https://github.com/pyinvoke/invoke
"""

from __future__ import absolute_import, print_function

# -----------------------------------------------------------------------------
# BOOTSTRAP PATH: Use provided vendor bundle if "invoke" is not installed
# -----------------------------------------------------------------------------
from . import _setup    # pylint: disable=wrong-import-order
INVOKE_MINVERSION = "0.14.0"
_setup.setup_path()
_setup.require_invoke_minversion(INVOKE_MINVERSION)

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
import sys
import os.path
from invoke import task, Collection
from invoke.util import cd
from path import Path
from contextlib import contextmanager

# -- TASK-LIBRARY:
from . import clean
from . import cmake
from . import test
# DISABLED: from . import docs
# DISABLED: from . import release

# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
@task
def init(ctx):
    """Initialize everything."""
    cmake.init(ctx)


@task
def reinit(ctx):
    """Reinitialize everything."""
    clean.clean(ctx)
    init(ctx)

@task(aliases=["examples"])
def cmake_examples(ctx, build_config=None):
    """Build CMake examples."""
    build_config = build_config or "Debug"
    with cd("examples/"):
        ctx.run("make BUILD_CONFIG={0}".format(build_config))


# -----------------------------------------------------------------------------
# TASK CONFIGURATION:
# -----------------------------------------------------------------------------
namespace = Collection()
namespace.add_task(clean.clean)
namespace.add_task(clean.clean_all)
namespace.add_task(init)
namespace.add_task(reinit)
namespace.add_task(cmake_examples)
namespace.add_task(cmake.test, name="ctest")
namespace.add_collection(Collection.from_module(cmake))
namespace.add_collection(Collection.from_module(test))
# DISABLED: namespace.add_collection(Collection.from_module(docs))
# DISABLED: namespace.add_collection(Collection.from_module(release))

# -- INJECT: clean configuration into this namespace
namespace.configure(clean.namespace.configuration())
if sys.platform.startswith("win"):
    # -- OVERRIDE SETTINGS: For platform=win32, ... (Windows)
    from ._compat_shutil import which
    run_settings = dict(echo=True, pty=False, shell=which("cmd"))
    namespace.configure({"run": run_settings})
