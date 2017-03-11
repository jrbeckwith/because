
    def init(self):
        self.status_dialog = QMessageBox(self)
        self.status_dialog.setStandardButtons(QMessageBox.Cancel)
        self.status_dialog.setWindowTitle("Because is Busy")
        # self.status_dialog.cancel

    def busy(self, text):
        """Called to display some busy or progress indicator.
        """
        self.status_dialog.setText(text)
        self.status_dialog.show()

    def cancel(self):
        """What happens when users asks to cancel pending request(s).
        """
        self.status_dialog.hide()

