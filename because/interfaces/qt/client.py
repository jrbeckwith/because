"""Client implementation for PyQt.

This implementation has the following features specific to the PyQt
environment.

* It abstracts many Qt details like QNetworkAccessManager, QSsl stuff,
  QNetworkRequest and QNetworkReply so that code for things like managing
  login tokens, generating requests and parsing responses can be reused in
  non-Qt environments.

* This includes carefully holding and dropping references to prevent 
  PyQt objects from being prematurely collected, which tends to generate
  bizarre behavior and SEGFAULTs at obscure times.

* It provides for Qt parents to be set.

* It exposes Qt signals so that they can be connected to other Qt signals and
  slots (this being the Qt idiom for async and communication across threads).
"""

import logging
from typing import (
    Any,
    Optional,
)
try:
    from PyQt5.QtNetwork import (
        QNetworkAccessManager,
        QNetworkRequest,
        QNetworkReply,
    )
    from PyQt5.QtCore import (
        QObject,
        QUrl,
        QByteArray,
        QBuffer,
        QIODevice,
        pyqtSignal,
    )
except ImportError:
    from PyQt4.QtNetwork import (
        QNetworkAccessManager,
        QNetworkRequest,
        QNetworkReply,
    )
    from PyQt4.QtCore import (
        QObject,
        QUrl,
        QByteArray,
        QBuffer,
        QIODevice,
        pyqtSignal,
    )
from because.request import Request, InvalidRequest
from because.client import Client as _Client
from . ssl_config import SSLConfig
from . response import Response, unpack_qnetworkreply
from . transfer import Transfer

LOG = logging.getLogger(__name__)


def pack_request(request, ssl_config):
    """Create a QNetworkRequest
    """
    if not isinstance(request.url, bytes):
        # No great exception to raise here
        return None

    from . ssl_config import SSLConfig as QtSSLConfig
    assert isinstance(ssl_config, QtSSLConfig)

    # PyQt5 specifically wants text.
    if not isinstance(request.url, str):
        url = request.url.decode("utf-8")
    else:
        url = request.url
    q_url = QUrl(url)
    q_request = QNetworkRequest(q_url)

    # Set headers on the request.
    # We use setRawHeader to avoid looking up header-name constants.
    for header_name, header_value in request.headers.pairs():
        q_request.setRawHeader(header_name, header_value)

    # Set SSL configuration (SSLConfig hides many details).
    q_request.setSslConfiguration(ssl_config._q_ssl_config)

    return q_request


class Client(_Client):
    """Make HTTP requests according to a specified policy.
    """
    #: Transfer implementation used by this class.
    transfer_cls = Transfer
    ssl_config_cls = SSLConfig

    #: default logger for this class.
    log = LOG.getChild("Client")

    def __init__(
            self,
            ssl_config=None,
            log=None,
            qnam=None,
            parent=None,
    ):
        # type: (SSLConfig, logging.Logger, QNetworkAccessManager, QObject) -> None
        """
        :arg ssl_config:
            Optional. SSLConfig instance to use.
        :arg log:
            Optional. Logger to use. Defaults to logger .qt.client.Client.
        :arg qnam:
            Optional. A QNetworkAccessManager to be used by this client. If
            None is passed, the QNAM will be created automatically.
        :arg parent:
            Optional. A QObject to pass as the parent when creating a QNAM or
            other objects.
        """

        # TODO: replace these with super call
        self.log = log or self.log
        self.ssl_config = ssl_config or self.ssl_config_cls()

        # In Qt, we need this thing to do POST requests and connect to some
        # basic signals. NOTE: Outside QGIS, this won't work without e.g.
        # QCoreApplication([]) first.
        # This doubles as a way for the caller to connect QNAM signals, since
        # they can create QNAM, connect signals then pass it in here.
        if not qnam:
            if not parent:
                qnam = QNetworkAccessManager()
            else:
                qnam = QNetworkAccessManager(parent)
            self._qnam = qnam

        # This is needed so Client knows when responses are done.
        qnam.finished.connect(self._finished)

        # Associate pending QNetworkReply with Transfers that wrap them,
        # so that QNAM finished signals can call into the right Transfer.
        # Maybe also so QObjects on the Transfer aren't collected prematurely.
        self.transfers = {}  # type: dict[QNetworkReply, Transfer]

    def _finished(self, reply):
        # type: (QNetworkReply) -> None
        """Receive notification of finished requests.
        """
        # Normally QNetworkReply signals should be connected to slots on
        # Transfer, but I'm not sure if that is subject to race conditions
        # where finished events may fire before those signals are connected; if
        # so, this is a last resort to be certain no finished events leak.
        transfer = self.transfers.get(reply)
        if not transfer:
            return

        # response = unpack_qnetworkreply(reply)
        # ugh
        # transfer.response = response
        # transfer.on_finished()
        # NOTE: transfer has to be responsible for cleanup like
        # reply.deleteLater(), otherwise its callback will be called after
        # transfer.close() and fail because the reply was invalidated.
        # q_reply.deleteLater()
        # transfer.close()

    def transfer(self, request, log=None):
        # type: (Request, logging.Logger) -> Any
        """Create a Transfer object tied to this client for the given request.

        The transfer is not started.

        This hides Qt implementation details like the QNetworkRequest, the SSL
        config, and QNAM sendCustomRequest. Transfer just gets a function it
        can call to send body data.

        Unfortunately, Transfer has to hold references to QBuffer and
        QByteArray. So to avoid passing them from the client, transfer builds
        them itself and passes the QBuffer to this internal callback, which
        also minimizes the visibility of QBuffer to Client on the way to
        sendCustomRequest.
        """

        # To allow a transfer.start()
        # * Share QNAM, transfer knows to call its sendCustomRequest
        #   * Caller has to know it is using a QNAM
        #   * Exposes everything else on QNAM
        #   * Exposes QNetworkRequest
        #   * Exposes QBuffer
        # * Share QNAM's sendCustomRequest bound method
        #   * Exposes QNetworkRequest
        #   * Exposes QBuffer
        # * Share client itself, with some public method for transfer to call
        # * Share a callback that closes over Qt objects
        #   * Still exposes QBuffer, unless....

        # * We need a QNetworkRequest to give to QNetworkManager.
        # * QNetworkRequest needs a QUrl, not a Python string.
        # * It doesn't take other constructor parameters, use .setWhatever().
        # * QNetworkRequest doesn't take a parent.

        q_request = pack_request(request, self.ssl_config)

        class Nonlocal:
            transfer = None  # type: Optional[Transfer]

        def send_body(q_buffer):
            # type: (QBuffer) -> None
            """
            Have Qt send the request.
            Encapsulates QNAM and used to ensure the encapsulation of
            QNetworkRequest and QNetworkReply, such that Transfer only knows
            about QBuffer (since we need to hold a reference to it and Transfer
            is a natural place for that).
            """
            # Using sendCustomRequest for convenience: it allows an arbitrary
            # HTTP method, so we can represent that explicitly in our own
            # request representation and avoid if/elif/elif...
            q_reply = self._qnam.sendCustomRequest(
                q_request, request.method, q_buffer,
            )
            # Associate the QNetworkReply to a Transfer... I'm not sure I need
            # this, and it doesn't necessarily fix the race described below.
            # BUT Client needs to hold a reference to the Transfer to prevent
            # it and the Qt objects it holds refs to from being collected.
            self.transfers[q_reply] = Nonlocal.transfer
            return q_reply

            # NOTE: there MAY be a gap of time between the call to
            # sendCustomRequest and the connection of the QNetworkReply signals
            # to handlers, such that some signals pertaining to the request
            # aren't handled as expected.
            #
            # QNAM has signals that can be presubscribed to avoid this gap,
            # but there may still be a gap of time between the call to
            # sendCustomRequest and a QNetworkReply being associated to other
            # data, putting us right back at the same race condition.

        # Make the Transfer instance
        transfer = Transfer(
            request=request,
            log=self.log,
            # TODO: how to replace this?
            _send=send_body,
        )

        # Share this instance with the closure already given to the transfer,
        # so that it can associate the transfer to the returned QNetworkReply.
        #
        # While I'd rather not expose QNetworkReply to Client at all, we do
        # need to hold references to e.g. QByteArray to prevent them from being
        # collected until the Transfer is finished.
        # The transfer is a more logical place to keep these than client.
        Nonlocal.transfer = transfer

        # TODO: Transfer can connect to signals on the reply returned by the
        # callback.
        # If it were not for the need to hold references, we could nuke these
        # QNetworkReply to Transfer mappings as soon as the transfer's signals
        # were all connected...

        return transfer
