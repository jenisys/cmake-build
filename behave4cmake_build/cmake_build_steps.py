from behave import given, when, then, step
from behave4cmd0 import command_util
from invoke.util import cd
from path import Path


@when(u'I run "{command}" in directory "{directory}"')
def step_i_run_command(ctx, command, directory):
    """Run a command as subprocess in another directory,
    collect its output and returncode.
    """
    command_util.ensure_workdir_exists(ctx)
    workdir2 = Path(directory)
    if not workdir2.isabs():
        # -- USE: WORKDIR
        workdir2 = Path(ctx.workdir)/directory
    if not workdir2.isdir():
        assert False, "NEW WORKDIR={0} does not exists".format(workdir2.relpath())

    with cd(workdir2):
        # print("RUN: {0} (cwd={1})".format(command, Path(".").abspath()))
        text = u'When I run "{0}"'.format(command)
        ctx.execute_steps(text)
        # print("RUN.END: {0} (cwd={1})".format(command, Path(".").abspath()))
