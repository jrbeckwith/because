"""Routing demo dialog.
"""
import os
from datetime import datetime as Datetime
try:
    from PyQt5.QtCore import (
        pyqtSlot,
        pyqtSignal,
        QObject,
        QThread,
        QUrl,
    )
    from PyQt5.QtNetwork import (
        QNetworkRequest,
        QNetworkReply,
    )
except ImportError:
    from PyQt4.QtCore import (
        pyqtSlot,
        pyqtSignal,
        QObject,
        QThread,
        QUrl,
    )
    from PyQt4.QtNetwork import (
        QNetworkRequest,
        QNetworkReply,
    )
from . dialog import Dialog
from . transfer_dialog import TransferDialog
from . transfer_worker import TransferWorker

HERE = os.path.abspath(os.path.dirname(__file__))


class RoutingTransferDialog(TransferDialog):
    """Manages the transfer process.
    """
    started = pyqtSignal()
    finished = pyqtSignal()

    def init(self):
        super(RoutingTransferDialog, self).init()
        self.setWindowTitle("Because Routing")
        self.label.setText("Requesting route...")
        self.start()
        self.show()

    def start(self):
        """Run the routing request using parameters.
        """
        # TODO: do something with parameters

        verb = "GET"
        url = "https://google.com/"
        qUrl = QUrl(url)
        qRequest = QNetworkRequest(qUrl)
        self.qRequest = qRequest
        qReply = self.client.qnam.sendCustomRequest(qRequest, verb, None)

        # Create a thread and worker for the transfer

        # QThread* thread = new QThread;
        self.thread = QThread(self, objectName="routingTransferThread")

        # Worker* worker = new Worker();
        # docs say: "The object cannot be moved if it has a parent."
        self.worker = TransferWorker(qReply)

        # worker->moveToThread(thread);
        self.worker.moveToThread(self.thread)

        # When QNetworkReply is finished, worker emits this with its QReply
        self.worker.received.connect(self.receive)

        self.worker.updated.connect(self.update)
        # connect(worker, SIGNAL (error(QString)), this, SLOT (errorString(QString)));
        # self.worker.errored.connect(self.error)
        # connect(thread, SIGNAL (started()), worker, SLOT (process()));
        self.thread.started.connect(self.worker.run)
        # connect(worker, SIGNAL (finished()), thread, SLOT (quit()));
        # self.worker.finished.connect(self.thread.quit)
        # connect(worker, SIGNAL (finished()), worker, SLOT (deleteLater()));
        # self.worker.finished.connect(self.worker.deleteLater)
        # connect(thread, SIGNAL (finished()), thread, SLOT (deleteLater()));
        # self.thread.finished.connect(self.thread.deleteLater)
        # thread->start();
        self.thread.start()

    def cancel(self):
        """User-initiated cancellation during request.
        """
        if self.worker:
            self.worker.abort()
            self.thread.quit()
        # TODO abort pending request
        self.hide()
        self.finished.emit()
        # self.deleteLater()

    # @pyqtSlot(int)
    def error(self, code):
        self.echo("Error: %s" % code)

    @pyqtSlot(QNetworkReply)
    def receive(self, reply):
        """Called when pending request is finished.

        :arg reply:
            A QNetworkReply representing the response.
        """
        data = reply.readAll()
        self.warning("!", "Received! %s" % data)
        self.hide()
        self.finished.emit()
        self.deleteLater()

    @pyqtSlot(int)
    def update(self, phase, current, maximum):
        self.progressBar.setValue(current)

    def finish(self):
        endTime = Datetime.utcnow()
        seconds = (endTime - self.startTime).total_seconds()
        self.hide()
        self.warning("Debug", "Done in %s seconds" % seconds)


class RoutingDialog(Dialog):
    """
    This dialog presents inputs so that users can provide parameters.
    When valid parameters are submitted, it delegates to RoutingTransferDialog.
    """

    # Functions for retrieving values from a UI form
    fieldExtractors = {
        "layerName": lambda ui: ui.layerName.text().strip(),
        "serviceName": lambda ui: ui.serviceChoice.currentText().lower(),
        "origin": lambda ui: ui.originAddress.text().strip(),
        "destination": lambda ui: ui.destinationAddress.text().strip(),
    }

    # Expected types for values extracted from UI form
    fieldTypes = {
        "layerName": type(u""),
        "serviceName": type(u""),
        "origin": type(u""),
        "destination": type(u""),
    }

    def __init__(self, parent, iface, client):
        """
        :arg parent:
            QObject to be used as the dialog's Qt parent.
        :arg iface:
            QgisInterface to be used to access QGIS UI.
        :arg client:
            because.qt.Client used to access Boundless services.
        """
        super(RoutingDialog, self).__init__(
            parent=parent, iface=iface, client=client,
            title="Because Routing",
            uiPath=os.path.join(HERE, "routing.ui"),
        )
        self.fieldExtractors = self.fieldExtractors.copy()
        self.fieldTypes = self.fieldTypes.copy()
        self.transferDialog = None

    def init(self):
        # QDialogButtonBox defined in routing.ui
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def getParameters(self):
        parameters = {}
        for fieldName, extractor in self.fieldExtractors.items():
            try:
                extracted = extractor(self)
            except AttributeError:
                extracted = None
            parameters[fieldName] = extracted
        return parameters

    def accept(self):
        """What to do when the user hits OK.

        This extracts parameters from the UI input widgets, then validates
        them. If they are valid, it delegates the rest to a TransferDialog.
        """
        # Read input widgets to get a set of parameters
        parameters = self.getParameters()

        # Check that the parameters are usable
        overallErrors, fieldErrors = self.validateParameters(parameters)

        # If parameters aren't usable, show user a warning.
        # This should be a bit disruptive; if we just fail silently, user has
        # no way of knowing why.
        if overallErrors or fieldErrors:
            errorText = self.errorText(overallErrors, fieldErrors)
            self.warning("Invalid Parameters", errorText)

            # Ensure we don't do anything else, like hiding the dialog
            return

        # But if parameters look good, go ahead and kick off a request
        else:
            # Create a dialog that will View-Control the transfer process
            # This is 1:1 with a transfer, subscribes to QNetworkReply signals
            # so that the form dialog doesn't need to know anything more
            self.transferDialog = RoutingTransferDialog(
                parent=self, iface=self.iface, client=self.client,
                parameters=parameters,
            )
            # TODO: compose a request *because.services.routing.request*
            # TODO: kick off a request pointing to callback *because.qt.client*
            # TODO: wire up response to a ProgressDialog

            self.hide()
