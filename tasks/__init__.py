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
import os.path
import sys
INVOKE_MINVERSION = "1.2.0"
_setup.setup_path()
_setup.require_invoke_minversion(INVOKE_MINVERSION)

TOPDIR = os.path.join(os.path.dirname(__file__), "..")
TOPDIR = os.path.abspath(TOPDIR)
sys.path.insert(0, TOPDIR)

# -----------------------------------------------------------------------------
# IMPORTS:
# -----------------------------------------------------------------------------
# import sys
from invoke import task, Collection
from invoke.util import cd

# -- TASK-LIBRARY:
# from . import clean
from . import invoke_cleanup as cleanup
from . import test
from cmake_build import tasks as cmake_build
# DISABLED: from . import docs
# DISABLED: from . import release

# -----------------------------------------------------------------------------
# TASKS:
# -----------------------------------------------------------------------------
@task
def init(ctx):
    """Initialize everything."""
    cmake_build.init(ctx)


@task
def reinit(ctx):
    """Reinitialize everything."""
    cleanup.clean(ctx)
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
namespace.add_collection(Collection.from_module(cleanup), name="cleanup")
namespace.add_task(init)
namespace.add_task(reinit)
namespace.add_task(cmake_examples)
namespace.add_collection(Collection.from_module(test))
namespace.add_collection(Collection.from_module(cmake_build, name="cmake"))
# DISABLED: namespace.add_collection(Collection.from_module(docs))
# DISABLED: namespace.add_collection(Collection.from_module(release))

cleanup.cleanup_tasks.add_task(cleanup.clean_python)

# -- INJECT: clean configuration into this namespace
namespace.configure(cleanup.namespace.configuration())
if sys.platform.startswith("win"):
    # -- OVERRIDE SETTINGS: For platform=win32, ... (Windows)
    from ._compat_shutil import which
    run_settings = dict(echo=True, pty=False, shell=which("cmd"))
    namespace.configure({"run": run_settings})
else:
    namespace.configure({"run": dict(echo=True, pty=True)})
