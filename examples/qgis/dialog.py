"""Base dialog implementation to reduce copy-paste repetition in demo dialogs.
"""

import collections
from datetime import datetime as Datetime
try:
    from PyQt5 import uic
    from PyQt5.QtCore import (
        QThread,
    )
    from PyQt5.QtGui import (
        QDialog,
        QMessageBox,
    )
except ImportError:
    from PyQt4 import uic
    from PyQt4.QtCore import (
        QThread,
    )
    from PyQt4.QtGui import (
        QDialog,
        QMessageBox,
    )


class Dialog(QDialog):
    """Common base implementation for dialogs in this module.
    """

    def __init__(self, parent, iface, client=None, title=None, uiPath=None):
        self.parent = parent
        self.iface = iface
        self.title = title
        self.uiPath = uiPath
        self.client = client

        super(Dialog, self).__init__(parent)
        if uiPath is not None:
            uic.loadUi(uiPath, self)
        if title is not None:
            self.setWindowTitle(title)
        self.init()

    def echo(self, message):
        """Cheap debug tool
        """
        now = Datetime.utcnow()
        messageBar = self.iface.messageBar()
        threadName = QThread.currentThread().objectName()
        messageBar.pushMessage(threadName, "[%s] %s" % (now, message))

    def init(self):
        """Steps to execute at the end of __init__.
        """

    def activate(self):
        """Define what happens every time this dialog is activated by a signal.
        """
        self.show()
        self.raise_()

    def reject(self):
        """Define what happens when the Cancel button is hit.
        """
        self.hide()

    def accept(self):
        """Define what happens when the OK button is hit.
        """
        self.hide()

    def getParameters(self):
        """Collect parameters from UI widgets.
        """
        # Subclasses should override this.
        return {}

    def validateParameters(self, parameters):
        """Validate parameter set.
        """
        overallErrors = []
        fieldErrors = collections.defaultdict(list)
        if not parameters:
            overallErrors.append("no parameters")
        for fieldName, expectedType in self.fieldTypes.items():
            try:
                value = parameters[fieldName]
            except KeyError:
                fieldErrors[fieldName] = "no value" % fieldName
                continue
            if not value:
                fieldErrors[fieldName] = "empty value"
            elif not isinstance(value, expectedType):
                type_ = type(value)
                fieldErrors[fieldName] = "unexpected type %r" % type_
        return overallErrors, fieldErrors

    def errorText(
            self, overallErrors, fieldErrors,
            prefix="Found the following input errors:",
            suffix="Please fix the errors and try again.",
    ):
        """Generate a blob of text representing the given errors.
        """

        lines = []
        if prefix:
            lines.extend([prefix, ""])
        lines.extend([
            "* %s" % error for error in overallErrors
        ])
        lines.extend([
            "* %s: %s" % (fieldName, error)
            for fieldName, error in fieldErrors.items()
        ])
        if suffix:
            lines.extend(["", suffix])
        return "\n".join(lines)

    def warning(self, title, message):
        QMessageBox.warning(self, title, message)
