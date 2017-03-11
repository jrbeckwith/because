"""Geocoding demo dialog.
"""
import os
from . dialog import Dialog

HERE = os.path.abspath(os.path.dirname(__file__))


class GeocodingDialog(Dialog):
    """Example dialog for use of Boundless geocoding service via because
    """
    def __init__(self, parent, iface, client):
        super(GeocodingDialog, self).__init__(
            parent=parent, iface=iface, client=client,
            title="Because Geocoding",
            uiPath=os.path.join(HERE, "geocoding.ui"),
        )

    def init(self):
        # self.client = Client()

        # QDialogButtonBox defined in geocoding.ui
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def accept(self):
        pass
