"""Root module for an example QGIS plugin.
"""
def classFactory(iface):
    """QGIS calls this with iface to create the plugin object.
    """
    # Here we are putting the plugin code in a separate plugin.py
    from . plugin import Plugin
    return Plugin(iface)
