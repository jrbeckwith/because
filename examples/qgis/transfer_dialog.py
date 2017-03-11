import os
from datetime import datetime as Datetime

try:
    from PyQt5.QtCore import (
        pyqtSlot,
        pyqtSignal,
    )
    from PyQt5.QtNetwork import (
        QNetworkReply,
    )
except ImportError:
    from PyQt4.QtCore import (
        pyqtSlot,
        pyqtSignal,
    )
    from PyQt4.QtNetwork import (
        QNetworkReply,
    )

from . dialog import Dialog

HERE = os.path.abspath(os.path.dirname(__file__))


class TransferDialog(Dialog):
    received = pyqtSignal(QNetworkReply)

    def __init__(self, parent, client, iface, parameters):
        self.parameters = parameters
        super(TransferDialog, self).__init__(
            parent=parent, iface=iface, client=client,
            title="Transfer Progress",
            uiPath=os.path.join(HERE, "progress.ui"),
        )
        # Show a simple busy indicator that doesn't need update signals
        # (progressBar is defined in progress.ui)
        self.progressBar.setMinimum(0)
        # self.progressBar.setMaximum(0)
        self.progressBar.setMaximum(100)

    def init(self):
        # Intercept cancel signals so we can abort pending request
        self.buttonBox.rejected.connect(self.cancel)
        # Start out with no progress
        self.progressBar.setValue(0)
        # Note the start time
        self.startTime = Datetime.utcnow()

    def run(self):
        """Start running the request.
        """
        # Override me!
        pass

    def cancel(self):
        """User-initiated cancellation during request.
        """
        # Override me!
        self.hide()

    @pyqtSlot(QNetworkReply)
    def receive(self, reply):
        """Called when pending request is finished.

        :arg reply:
            A QNetworkReply representing the response.
        """
        # Override me!
        self.hide()
