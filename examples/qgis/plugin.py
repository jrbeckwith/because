"""Module containing implementation of an example QGIS plugin.
"""
import os
try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtNetwork import (
        QNetworkAccessManager,
    )
    from PyQt5.QtGui import (
        QAction,
        QDialog,
        QMessageBox,
    )
    from PyQt5 import uic
except ImportError:
    from PyQt4.QtCore import Qt
    from PyQt4.QtNetwork import (
        QNetworkAccessManager,
    )
    from PyQt4.QtGui import (
        QAction,
        QDialog,
        QMessageBox,
    )
    from PyQt4 import uic
# from qgis.core import QgsNetworkAccessManager

# from because.qt import Client
from . routing_dialog import RoutingDialog
from . geocoding_dialog import GeocodingDialog
from . basemaps_dialog import BasemapsDialog


HERE = os.path.abspath(os.path.dirname(__file__))


class Plugin(object):
    """Class containing implementation of a QGIS plugin.
    """

    def __init__(self, iface):
        """
        """
        # Store the iface passed by QGIS via classFactory.
        self.iface = iface

        # Used to hold references to QActions and QDialogs
        self.actions = []
        self.dialogs = []

        # Submenu name passed to addPluginToWebMenu and removePluginWebMenu
        self.menu_name = "Because Example"

        # Object used to make requests to BCS APIs
        # TODO use Qgs
        class Client(object):
            pass
        client = Client()
        # client.qnam = QgsNetworkAccessManager.instance()
        client.qnam = QNetworkAccessManager()
        self.client = client

    def initGui(self):
        """Called by QGIS to set up the GUI.

        Interactions with the Qt/GUI environment, like messing with menus,
        dialogs, actions, and signals, should be isolated to this method
        instead of __init__. The corresponding cleanups should happen in
        unload().
        """
        # Define names and implementations for each demo dialog
        dialog_classes = {
            "Basemaps": BasemapsDialog,
            "Geocoding": GeocodingDialog,
            "Routing": RoutingDialog,
        }

        # Get the window to use as the Qt parent for actions and dialogs
        window = self.iface.mainWindow()

        # Create instances of each demo dialog class
        dialogs = {}
        for dialog_name, dialog_cls in sorted(dialog_classes.items()):
            dialogs[dialog_name] = dialog_cls(window, self.iface, self.client)

        # Create QActions for triggering each dialog
        actions = {}
        for dialog_name in sorted(dialogs.keys()):
            actions[dialog_name] = QAction(dialog_name, window)

        # Connect QAction triggered signals to activate methods on dialogs
        for name, action in actions.items():
            dialog = dialogs[name]
            action.triggered.connect(dialog.activate)

        # Create the menu and add all the actions to it, in sort order
        for _, action in sorted(actions.items()):
            self.iface.addPluginToWebMenu(self.menu_name, action)

        # Hold references to Qt objects
        self.dialogs = dialogs
        self.actions = actions

    def unload(self):
        """Called by QGIS to tear down the plugin's state.
        """
        # Mark Qt objects for destruction by event loop
        for action in self.actions.values():
            self.iface.removePluginWebMenu(self.menu_name, action)
            action.deleteLater()
        for dialog in self.dialogs.values():
            dialog.deleteLater()

        # Break references to Qt objects just in case
        self.dialogs = None
        self.actions = None
