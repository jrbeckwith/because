"""Base future interfaces/traits.
"""
import sys
from typing import (
    Any,
)


class Future(object):
    """Base class for the version-portable future-like objects used in because.

    Subclass __init__ may have any signature and is not required to call super
    __init__. After all, it is the instances which must be substitutable.
    """

    def start(self):
        # type: () -> None
        """Start work without blocking.

        This method provides a way for the caller to cue the future that it is
        about to do other things during which it would like progress to be
        made, if possible.

        The contract of this class, especially this method, is very particular
        about when futures should do "real work." For present purposes, "real
        work" is defined as anything which involves I/O waits, significant lock
        waits, significant amounts of compute time, or externally visible side
        effects.

        Avoiding real work in __init__ allows execution to be deferred until
        after construction. This allows us to go ahead and create the
        representation of the work to be performed ahead of performing it,
        whenever it's convenient; so we don't have to hold separate
        representations of work to be done.

        In particular, a future should not do real work unless and until the
        first call to start(). If the future can make background progress at
        this time, then it should begin work. But that work should never block
        start() itself from returning as soon as it reasonably can. And any
        real work that the future cannot make background progress on should not
        be done in start(). So if the future cannot really do anything without
        blocking, it should just ignore start().

        This preserves the usefulness of start() as a mere cue to start
        working, and avoids encouraging usages which rely on blocking
        implementations by skipping calls to wait() or the like.
        """

    def wait(self):
        # type: () -> Any
        """Block until the future is ready, then return its result.

        Subclasses have to decide how to implement this. For blocking
        implementations, this is the only way to get a result. For asynchronous
        implementations, blocking is usually undesirable and so this should
        almost never be called; but sometimes it is useful to have an adapter
        from an asynchronous world to a synchronous world, and providing this
        allows blocking implementations as a "lowest common denominator."

        The base class method returns self, but others will generally want to
        return whatever the future computed instead.
        """
        return self

    def cancel(self):
        # type: () -> bool
        """Attempt to cancel any ongoing work.

        This is primarily a way to communicate to the future that any ongoing
        work should be stopped if reasonably possible. No guarantees are made
        as to the resulting state, or whether canceling is a good idea;
        though the future might ignore cancels if they are a bad idea.

        If the future had no problem canceling ongoing work, this should return
        True. If it couldn't be canceled, this should return False.
        """
        # TODO: but is it allowed to block? curio just exposes a parameter.
        return False

    def close(self):
        # type: () -> None
        """Clean up state.

        This method is not guaranteed to be called unless the instance is used
        as a context manager (even then, the process can crash or the power can
        go out).
        """

    def __enter__(self):
        # type: () -> Future
        """Called when entering the context managed by this instance.

        Along with __exit__, this permits usage of the Future as a context
        manager, permitting deterministic cleanup.

        This method may block. Individual futures can customize what they
        return here, and may normally block to get the needed result.

        In Python 3.5, "async with" can be supported with an __aenter__ method
        to allow the caller to wait locally without globally blocking.
        """
        return self.wait()

    def __exit__(self, exception_type, exception, traceback):
        """Called when editing the context managed by this instance.

        Along with __enter__, this permits usage of the Future as a context
        manager, permitting deterministic cleanup.

        This method may block. If this future was not waited on, then the close
        may prevent or cancel it, or it may wait until it is completed before
        this method returns.

        In Python 3.5, "async with" can be supported with an __aexit__ method
        to allow the caller to wait locally for the exit without globally
        blocking.
        """
        self.close()
        return None


if sys.version_info >= (3, 0):
    from . _future_py3 import Result, Present
else:
    from . _future_py2 import Result, Present


__all__ = ["Future", "Present", "Result"]
