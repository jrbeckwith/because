"""Example of how to use because from a PyQt application.
"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit, QLabel,
    QLineEdit,
)
from because import Because


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        # Set a title and comfortable minimum size for the window.
        self.setWindowTitle("Because Qt Demo")
        self.setMinimumWidth(1024)
        self.setMinimumHeight(768)

        # Create boxes allowing a username and password to be put in.
        self.usernameLabel = QLabel("Email", self)
        self.usernameInput = QLineEdit(self)
        self.usernameInput.setPlaceholderText("my@emailaddress.com")
        self.usernameInput.setFocus()

        self.passwordLabel = QLabel("Password")
        self.passwordInput = QLineEdit(self)
        self.passwordInput.setPlaceholderText("myConnectPassword")
        self.passwordInput.setEchoMode(QLineEdit.PasswordEchoOnEdit)

        # Create a button for triggering the login process.
        self.loginButton = QPushButton("Login", self)
        self.loginButton.clicked.connect(self.login)
        self.passwordInput.returnPressed.connect(self.loginButton.click)

        # Create an area to display text in.
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)

        # Lay everything out inside the window vertically.
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.usernameLabel)
        self.layout.addWidget(self.usernameInput)
        self.layout.addWidget(self.passwordLabel)
        self.layout.addWidget(self.passwordInput)
        self.layout.addWidget(self.loginButton)
        self.layout.addWidget(self.output)

        # Get a 'because' object. Note that the string "qt" is passed.
        # This asks because to use its qt interface/implementation
        self.because = Because("qt", "dev")

    def login(self):
        # Retrieve text and do very basic validation on it before proceeding
        username = self.usernameInput.text().strip()
        password = self.passwordInput.text().strip()
        if not username or not password:
            self.output.clear()
            self.output.append("Please provide both username and password!")
            return

        # Disable the button so the user doesn't spam it by accident
        self.loginButton.setEnabled(False)

        # Use because to login
        transfer = self.because.login(username, password)
        self.output.append(
            "Transfer started at {}".format(transfer.started_at)
        )

        # When using the Qt interface, the transfer object has signals
        # that you can connect slots to.
        transfer.signals.success.connect(self.showToken)
        transfer.signals.failure.connect(self.beSad)
        transfer.signals.uploadProgress.connect(self.showUploadProgress)
        transfer.signals.downloadProgress.connect(self.showDownloadProgress)

        # Hang on to this so we can play with it later
        self.transfer = transfer

        # Don't transfer.wait() because that blocks, freezing the thread!
        # Let the signals take care of it asynchronously.

    def showUploadProgress(self, count, total):
        """Demonstrate how to handle uploadProgress.

        This signal is forwarded from QNetworkReply.
        """
        self.output.append("Upload: {}/{}".format(count, total))

    def showDownloadProgress(self, count, total):
        """Demonstrate how to handle downloadProgress.

        This signal is forwarded from QNetworkReply.
        """
        self.output.append("Upload: {}/{}".format(count, total))

    def showToken(self):
        """Called when login succeeds.
        """
        # You wouldn't normally grab the token like this. It's stored as bytes.
        text = self.because.token.decode("ascii")
        self.output.append("Token: {}".format(text))
        self.output.append("Succeeded in {}s".format(self.transfer.duration()))

        # Re-enable the button
        self.loginButton.setEnabled(True)

    def beSad(self):
        self.output.append("An error occurred, which is sad.")
        self.output.append("Failed in {}s".format(self.transfer.duration()))

        # Re-enable the button
        self.loginButton.setEnabled(True)


def main():
    print(
        "If you happen to see messages like this:\n"
        "    qt.network.ssl: QSslSocket: cannot resolve SSLv2_client_method\n"
        "    qt.network.ssl: QSslSocket: cannot resolve SSLv2_server_method\n"
        "Then please feel free to ignore them. They are completely harmless.\n"
    )

    app = QApplication(sys.argv)
    window = Window()
    window.show()
    status = app.exec_()
    sys.exit(status)


# In a real application, you would want to keep this cruft out of your library
# modules, and make a separate script file that wouldn't need this check.
if __name__ == "__main__":
    main()
