try:
    from PyQt5.QtCore import (
        pyqtSignal,
        QObject,
        QThread,
    )
    from PyQt5.QtNetwork import (
        QNetworkReply,
    )
except ImportError:
    from PyQt4.QtCore import (
        pyqtSignal,
        QObject,
        QThread,
    )
    from PyQt4.QtNetwork import (
        QNetworkReply,
    )



class TransferWorker(QObject):
    # phase, current, maximum
    updated = pyqtSignal(str, int, int)

    # passthrough from QNetworkReply
    errored = pyqtSignal(QNetworkReply.NetworkError)

    # emitted by worker to hand off the reply when finished
    received = pyqtSignal(QNetworkReply)

    # passthrough from QNetworkReply
    finished = pyqtSignal()

    # docs say: "The object cannot be moved if it has a parent."
    # So don't even bother taking one.
    #
    # Additionally, you can't make a QNAM in the main thread and pass it here
    # to use. So just take qReply and mind the transfer process.
    #
    def __init__(self, qReply):
        super(TransferWorker, self).__init__()
        self.qReply = qReply

    def run(self):
        threadName = QThread.currentThread().objectName()
        print("TransferWorker.run starting %r" % threadName)
        qReply = self.qReply

        # Connect signals to pass through to TransferDialog
        qReply.downloadProgress.connect(self._download_progress)
        qReply.uploadProgress.connect(self._upload_progress)
        qReply.error.connect(self.errored)

        qReply.finished.connect(self.finish)

        print("TransferWorker.run exiting")

        # n.b.: we are not actually done until the qReply is done.

        # with open("/tmp/foo.txt", "w") as stream:
        #     import time
        #     for i in range(0, 101):
        #         stream.write("%s: %s\n" % (threadName, i))
        #         stream.flush()
        #         self.updated.emit(i)
        #         time.sleep(0.01)
        #     self.updated.emit(100)

    def abort(self):
        self.qReply.abort()

    def finish(self):
        self.received.emit(self.qReply)
        self.finished.emit()

    def _download_progress(self, current, maximum):
        print("_download_progress", current, maximum)
        self.updated.emit("download", current, maximum)

    def _upload_progress(self, current, maximum):
        print("_upload_progress", current, maximum)
        self.updated.emit("upload", current, maximum)
