"""Client implementation for QGIS.

This implementation has the following differences from the Qt implementation it
is based on.

* It uses a default QNAM of QgsNetworkAccessManager.instance(), which has some
  differences from QNetworkAccessManager, e.g. that QGIS decides its parent.
  However, an arbitrary QNetworkAccessManager can be created separately with
  whatever parent is desired, and passed explicitly as the QNAM if desired.
"""
import logging
from typing import (
    Any,
)
from qgis.core import QgsNetworkAccessManager
from .. qt.client import Client as _Client
from . transfer import Transfer


#: default logger for this module.
LOG = logging.getLogger(__name__)


class Client(_Client):
    """
    """
    #: Transfer implementation used by this class.
    transfer_cls = Transfer  # type: Any

    #: default logger for this class.
    log = LOG.getChild("Client")

    def __init__(
            self,
            ssl_config=None,
            log=None,
            qnam=None,
    ):
        """
        :arg ssl_config:
            Optional. SSLConfig instance to use.
        :arg log:
            Optional. Logger to use.
        :arg qnam:
            Optional. A QgsNetworkAccessManager or QNetworkAccessManager to be
            used by this client. If none is passed, the client will use the
            result returned by a call to QgsNetworkAccessManager.instance().
        """
        self.log = log or self.log

        # In QGIS, you can't necessarily instantiate QgsNetworkAccessManager,
        # e.g. "TypeError: qgis._core.QgsNetworkAccessManager cannot be
        # instantiated or sub-classed"
        if not qnam:
            qnam = QgsNetworkAccessManager.instance()

        super(Client, self).__init__(
            ssl_config=ssl_config,
            log=self.log,
            qnam=qnam,
            parent=None,
        )
