from typing import (
    Any,
    Callable,
)
from . future import Future


class _Present(Future):
    """Internal base class with common attributes for Present implementations.

    Subclasses will not inherit this docstring and should not use it. Instead,
    they should use _doc.
    """
    _doc = (
        """Returned when we need a future which always just gives a value.

        The value is just given away for free. It's a present, and all you have
        to do is unwrap it. The future is now!
        """
    )

    def __init__(self, value):
        self._value = value

    def wait(self):
        return self._value

    def cancel(self):
        """You cannot cancel a present, it already happened.
        """
        return False


class _Result(Future):
    """Internal base class with common attributes for Result implementations.

    Subclasses will not inherit this docstring and should not use it. Instead,
    they should use _doc.
    """
    _doc = (
        """A future which waits for another future, then applies a callback.
        """
    )

    def __init__(self, future, callback):
        # type: (Future, Callable) -> None
        """
        :arg original:
            The future this depends on.

            For example, a Transfer which returns a Response from wait().

        :arg callback:

            A callback which takes one argument. Whatever this returns will be
            returned by wait().

            For example, a parse function which takes a Response and returns a
            Route.
        """
        self._future = future
        self._callback = callback

        # State to handle cancels after callback started running
        self._running_callback = False

    def wait(self):
        # type: () -> Any
        """Block on the wrapped future, then apply the callback to it.
        """
        response = self._future.wait()
        self._running_callback = True
        return self._callback(response)

    def cancel(self):
        # type: () -> bool
        """Attempt to cancel the underlying future.

        Returns true if the underlying future was canceled, otherwise returns
        False. If the callback already started running, cancel will fail,
        returning False.
        """
        # We already finished the original and are already in the callback,
        # so tell the user they can't cancel any ongoing work now.
        # The caller of wait() will still receive its value, not some weird
        # CancelledError.
        if self._running_callback:
            return False
        return self._future.cancel()
