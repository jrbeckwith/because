"""Basemaps demo dialog.
"""
import os
from . dialog import Dialog
try:
    from PyQt4.QtGui import QMessageBox
except ImportError:
    from PyQt5.QtGui import QMessageBox
from qgis.core import (
    QgsMapLayerRegistry,
)
from because import Because
from because.interfaces.qgis.basemap_gdal import GDALBasemapLayer

HERE = os.path.abspath(os.path.dirname(__file__))


class BasemapsDialog(Dialog):
    """Example dialog for use of Boundless basemaps service via because
    """

    def __init__(self, parent, client, iface):
        super(BasemapsDialog, self).__init__(
            parent=parent, iface=iface, client=client,
            title="Because Basemaps",
            uiPath=os.path.join(HERE, "basemaps.ui"),
        )
        self.because = Because("qt", env="dev")
        self.basemaps_dict = None

    def init(self):
        self.populateButton.clicked.connect(self.populate)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def populate(self):
        if not self.basemaps_dict:
            # TODO: stop blocking. have to expose signals via Result. :/
            self.because.login("myusername", "mypassword").wait()
            self.basemaps_dict = self.because.basemaps().wait()

        self.basemapComboBox.clear()
        basemaps = sorted(self.basemaps_dict.values(), key=lambda m: m.title)
        for basemap in basemaps:
            if basemap.title == "Recent Imagery":
                continue
            if basemap.standard != "XYZ" or basemap.tile_format != "PNG":
                continue
            print(basemap.pretty_text())
            self.basemapComboBox.addItem(basemap.title)

    def accept(self):
        # TODO use the selected basemap
        chosen_basemap = str(self.basemapComboBox.currentText())
        if not chosen_basemap:
            QMessageBox.warning(
                self,
                "More input needed to continue",
                "Please populate the basemaps list first"
            )
            return

        basemap = self.basemaps_dict.get(chosen_basemap.lower())

        api_key = self.apiKeyInput.text()
        if not api_key:
            QMessageBox.warning(
                self,
                "More input needed to continue",
                "Please enter an API key"
            )
            return
        # In case newlines are pasted in, accidental invisible whitespace, etc.
        api_key = api_key.strip()

        # TODO: find instances of {-?} and flag them somewhere else where $ is
        # added.

        # TODO: ensure dollar signs to generate the URL, in the basemap impl
        # url = "http://api.dev.boundlessgeo.io/v1/basemaps/mapbox/streets/${z}/${x}/${y}.png"
        # url = "http://api.dev.boundlessgeo.io/v1/basemaps/boundless/osm/${x}/${y}/${z}.png"
        url = basemap.url
        if "{-" in url:
            url = url.replace("{-", "{")
            y_origin = "bottom"
        url = url.replace("{", "${")

        # TODO: do this in the endpoint instead!
        suffix = "?apikey={}".format(api_key)
        url = url + suffix
        print("url={0!r}".format(url))

        # TODO: use a method on the frontend
        #   which uses the service definition, as a first cut
        #   then dynamically construct endpoint instance to use

        layer = GDALBasemapLayer(
            url, basemap.title, "Because", y_origin=y_origin
        )
        registry = QgsMapLayerRegistry.instance()
        registry.addMapLayer(layer)

        self.hide()
