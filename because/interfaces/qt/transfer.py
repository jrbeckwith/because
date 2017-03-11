import logging
from datetime import datetime as Datetime
from typing import (
    Any,
    Callable,
)
try:
    from PyQt5.QtCore import (
        QObject,
        QEventLoop,
        QTimer,
        QByteArray,
        QBuffer,
        pyqtSignal,
    )
    from PyQt5.QtNetwork import (
        QNetworkRequest,
        QNetworkReply,
    )
except ImportError:
    from PyQt4.QtCore import (
        QObject,
        QEventLoop,
        QTimer,
        QByteArray,
        QBuffer,
        pyqtSignal,
    )
    from PyQt4.QtNetwork import (
        QNetworkRequest,
        QNetworkReply,
    )

from because.transfer import (
    Transfer as _Transfer,
    InvalidTransfer,
    TransferError,
)
from because.request import Request
from because.response import Response
from . ssl_config import SSLConfig

LOG = logging.getLogger(__name__)



def unpack_reply(reply):
    """Convert a QNetworkReply to a because.response.Response.

    :warning: This may destroy the state of the QNetworkReply, so don't use the
    QNetworkReply after calling this.

    :warning: The returned Response may not work properly if the QNetworkReply
    or objects it depends on are freed before the Response is used.

    You probably want to use Transfer instead of using this. This helper
    function is used in the implementation of Transfer, but is exposed
    separately as part of the lower-level API layer.
    """
    # TODO: return a TransferError to be raised

    error_text = reply.errorString()
    status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
    redirect = reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
    headers = [
        (bytes(key), value.data())
        for key, value in reply.rawHeaderPairs()
    ]

    # Read out data.
    # TODO: This technique isn't correct for big bodies...
    # probably need to pass along an iterator...
    # but this induces a number of lifetime issues...
    data = reply.readAll()

    # Convert from QByteArray to Python bytes
    body = bytes(data)

    response = Response(
        # error=error_text,
        # redirect=redirect,
        status=status,
        headers=headers,
        body=body,
    )
    # TODO: error
    return response, None


class TransferSignals(QObject):
    """Hold signals for an instance of interfaces.qt.Transfer.

    This is the QObject handling signals for Transfer, allowing Transfer itself
    not to be a QObject.

    Exposing these means not having to expose the QNetworkReply directly.
    """
    #: Forwarded from the QNetworkReply.
    uploadProgress = pyqtSignal("qint64", "qint64")

    #: Forwarded from the QNetworkReply.
    downloadProgress = pyqtSignal("qint64", "qint64")

    #: Emitted when a response is available on the transfer.
    success = pyqtSignal()

    #: Emitted when a response was unavailable for any reason.
    failure = pyqtSignal()
    # Hides QNetworkReply.error: QNetworkReply.NetworkError
    # Hides QNetworkReply.sslErrors

    #: Should be emitted for either a success or a failure.
    #: You should probably connect success and failure instead.
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super(TransferSignals, self).__init__(parent)
        self.reply = None

    def connect(self, reply):
        """Forward signals of the provided QNetworkReply.
        """
        # Only connect a given instance to one particular reply.
        if self.reply:
            return
        self.reply = reply

        # Forward signals.
        reply.uploadProgress.connect(self.uploadProgress)
        reply.downloadProgress.connect(self.downloadProgress)


class Transfer(_Transfer):
    """Hold per-request state for one ongoing HTTP request cycle.

    This is also used as a device for bundling up multiple descriptions of a
    transfer's state to be handled by one callback, instead of requiring many
    separate callbacks to handle many different state notifications.
    """
    ssl_config_cls = SSLConfig

    # n.b.: can't define signals here since this is not a QObject. The
    # workaround would be to have this instantiate a QObject subclass that
    # defines your signals. But the QNetworkReply already defines all the
    # signals we need here.

    log = LOG.getChild("Transfer")

    def __init__(
            self,
            request,
            ssl_config=None,
            log=None,
            _send=None,
    ):
        # type: (Request, SSLConfig, logging.Logger, Callable) -> None
        """
        :arg request:
            Request object describing the HTTP request to be performed.
        :arg ssl_config:
            SSLConfig for the performance of the request.
        :arg log:
            logger instance to use for logging messages.
        :arg _send:
            Internal: callable passed so that Transfer can initiate a request
            via Client's QNAM.
        """
        if not _send:
            raise InvalidTransfer(
                "qt Transfer must have _send to initiate requests with"
            )
        self._send = _send

        #: Exposes Qt signals for this Transfer instance.
        self.signals = TransferSignals()

        # Internal references to underlying Qt objects
        self._reply = None    # type: QNetworkReply
        self._array = None    # type: QByteArray
        self._buffer = None   # type: QBuffer
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timeout)
        # DO NOT start the timer until transfer.start()!

        # Used to ensure we only run on_finished once.
        self._ran_on_finished = False

        self._emitted = set()  # type: set[Any]

        # note: error is indicated per QNetworkReply.NetworkError enum

        super(Transfer, self).__init__(
            request=request,
            ssl_config=ssl_config,
            log=log,
        )

        # TODO: check for QNetworkReply.TimeoutError, ProxyTimeoutError

    def _set_reply(self, reply):
        """Associate to the given QNetworkReply and connect signals.
        """
        # We already did this reply
        if self._reply == reply:
            return

        # We already did a different reply.
        # We don't want confusion about which signals are for which. If we just
        # disconnected all the old signals, it would be confusing to their
        # subscribers to just silently stop firing.
        if self._reply is not None:
            raise TransferError(
                "Transfer instance is already associated with a QNetworkReply",
            )

        # Hang on to the QNetworkReply instance
        # * to ensure future calls don't associate to a different reply
        # * to prevent premature garbage collection
        self._reply = reply

        # Forward progress signals from QNetworkReply.
        self.signals.connect(reply)

        # Don't forward finished - only emit it when we have data to share.
        # Don't forward error, sslErrors - we want to aggregate these together
        # also include other errors not generated by Qt, and present them as
        # TransferError.

        # Connect reply signals to methods on Transfer which need to collect
        # response or error to give to caller. (By design, the QNetworkReply
        # itself is encapsulated so that receivers of its signals don't have
        # it, so Transfer has to provide a way of getting at the data.)
        reply.finished.connect(self._on_finished)
        reply.error.connect(self._on_error)
        reply.sslErrors.connect(self._on_ssl_errors)

    def _start_timer(self, timeout):
        """Start the timeout QTimer.
        """
        self._timer.start(timeout)

    def _stop_timer(self):
        """Stop the timeout QTimer.
        """
        if self._timer and self._timer.isActive():
            self._timer.stop()

    def _emit(self, signal):
        self._emitted.add(signal)
        signal.emit()

    def _on_error(self, code):
        """Handle an error detected during response processing.
        """
        # Collect the error data for diagnostics
        error_code = code
        error_text = self._reply.errorString()
        self.error = TransferError(
            code=error_code, text=error_text
        )
        # ^ We can't raise this yet, but maybe we can later...

        # Don't confuse matters with questionable response object
        self.response = None

        # Tell subscribers that things didn't go well
        # self.signals.failure.emit()
        self._emit(self.signals.failure)

    def _on_ssl_errors(self):
        # TODO: ensure this doesn't emit redundantly with on_error..
        # self.signals.failure.emit()
        self._emit(self.signals.failure)

    def _on_finished(self):
        """Handle reply finish: return Response or raise TransferError.

        This means that the end of the transfer is ready to be handled,
        response read, etc. whether or not there was an error.
        """
        # Prevent timeouts ASAP
        self._stop_timer()

        # Ensure this method only runs once (e.g. if it is triggered by the
        # QNAM finished signal). Otherwise, silly things may happen with data
        # reads, and also with the finished signal.
        if self._ran_on_finished:
            return
        self._ran_on_finished = True

        # If a Qt-level network error already occurred, don't try to unpack
        # and don't emit any new signals
        if self.error:
            return
        # However, we may find other errors here...

        # Unpack the QNetworkReply to create a Response; hold on to that
        try:
            response, error = unpack_reply(self._reply)
        except Exception as caught:
            response, error = None, caught

        self.response = response
        self.error = error

        if not error:
            # We don't just forward "finished" so that subscribers don't run
            # when the QNetworkReply is in but before we have response ready
            # for caller.
            self.signals.success.emit()
        else:
            self.signals.failure.emit()

        # Emit a courtesy finished in case that's all caller cares about
        self.signals.finished.emit()

    def start(self):
        # type: () -> None

        request = self.request
        # Pack the request body for Qt.
        # * sendCustomRequest needs a QIODevice.
        # * We can get one using QBuffer.
        # * QBuffer needs a QByteArray.
        # * TODO: extra copy and double memory usage?
        # * TODO: can QBuffer parent solve some problems? maybe use q_request?
        # * TODO: can we just pass q_array intending const QByteArray &data? or
        #   even just a python bytes? possible??
        array = QByteArray(request.body) if request.body else QByteArray()
        buf = QBuffer(array)

        # Call the function provided by Client to send the request body.
        reply = self._send(buf)

        # Connect QNetworkReply signals directly to callbacks on self.
        self._set_reply(reply)

        # Hold references to underlying Qt objects involved in response read.
        #
        # * If there is no reference to the QBuffer after this method exits,
        #   QGIS is likely to crash in short order.
        #
        # * If there is no reference to the QArray after this method exits, the
        #   result will be flaky; it may work, or silently fail, or crash QGIS.
        #
        #   Likely explanation: when the refcount goes to 0, Python collects
        #   the object, and then Qt reads inappropriately from the freed
        #   pointer, causing a SEGFAULT.
        #
        #   The read doesn't seem to be caused by the finished signal or any of
        #   our callbacks, because this crash happens even if those are all
        #   removed.
        self._buffer = buf
        self._array = array

        # Update base class state
        super(Transfer, self).start()

    def _on_timeout(self):
        """Handle the expiration of the deadline timer.
        """
        # Flag what happened
        self.timed_out = True

        # Halt ongoing work
        self.cancel()

        # Not cleaning up with close() in case there is postmortem to be done.

    def wait(self):
        """Wait synchronously for the transfer to finish.

        The method is offered and blocks to honor the base class contract.

        :warning: this function blocks, which isn't the right way to use Qt,
        because you are likely e.g. to make the GUI thread unresponsive.
        """
        loop = QEventLoop()
        # TODO: test if this is the right event, or .e.g. use readyRead?
        # TODO: handle timeout
        self._reply.finished.connect(loop.quit)
        loop.exec_()

        # Update base class state
        super(Transfer, self).wait()

        # I guess this works
        if self.error:
            raise self.error
        return self.response  # is there one though

    def _abort(self):
        # type: () -> None
        """Abort the QNetworkReply if it's running, otherwise do nothing.
        """
        if self._reply and self._reply.isRunning():
            self._reply.abort()

    def cancel(self):
        # type: () -> bool
        """Atttempt to stop all pending timers and activity.
        """
        # Prevent timeout callback firing ASAP
        self._stop_timer()

        # If we close while still running, we should abort any ongoing HTTP
        # request process. Yes, this is different from the Qt API abort(),
        # which is part of why we don't use that name for this operation.
        self._abort()

        # Update self.stopped_at etc.
        return super(Transfer, self).cancel()

        # NOTE: Teardown is *intentionally* left to close() since someone may
        # need to stop work and do a postmortem or restart somehow.

    def close(self):
        # type: () -> None
        """Cancel and disable the transfer and tear down state.
        """
        # If any work is ongoing, stop it
        self.cancel()

        # Close the QBuffer
        if self._buffer is not None:
            self._buffer.close()

        # Empty the QByteArray to prevent further access
        if self._array is not None:
            self._array.truncate(0)

        # Prevent further reads from the QNetworkReply
        if self._reply:
            self._reply.close()

        # Break references to ensure Qt objects can be collected
        self._timer = None
        self._buffer = None
        self._array = None
        self._reply = None

        # Tear down superclass state
        super(Transfer, self).close()
