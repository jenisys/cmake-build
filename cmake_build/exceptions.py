# -*- coding: UTF-8 -*-
"""
Common exception classes.
"""

from __future__ import absolute_import
from invoke.exceptions import UnexpectedExit
from invoke.runners import Result

# ---------------------------------------------------------------------------
# MORE INVOKE RELATED EXCEPTION CLASSES (needed for task related execution)
# ---------------------------------------------------------------------------
class NiceFailure(UnexpectedExit):
    """
    Can be used to fail a invoke task and leave the program with a nice error
    message (but without a traceback).

    Example:

    .. code-block:: python

        from __future__ import print_function
        from invoke import task

        @task
        def bad_hello(ctx, name="Alice"):
            print("Hello {0}".format(Alice))
            raise NiceFailure(reason="OOPS, fail here")
    """
    HIDE_NOTHING = "__NOTHING__"
    TEMPLATE = "FAILED: {reason} (in: {command})"

    def __init__(self, result=None, reason=None, template=None):
        template = template or self.TEMPLATE
        if result is None:
            result = Result(exited=1, hide=self.HIDE_NOTHING)
        if not result.hide:
            # -- HINT: WEIRD-TWEAK needed for output.
            # REQUIRES: Non-empty string or non-empty list/tuple.
            # SEE ALSO: invoke.program:Program.run() exception handling.
            result.hide = self.HIDE_NOTHING
        UnexpectedExit.__init__(self, result, reason or "FAILED")
        self.template = template

    def __str__(self):
        text = self.template.format(result=self.result, reason=self.reason,
                                    command=self.result.command)
        return text

    def __repr__(self):
        return "<%s: reason=%s, result=%s>" % \
               (self.__class__.__name__, self.reason, self.result)
