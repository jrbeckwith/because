===================
Example QGIS Plugin
===================

This example plugin demonstrates how QGIS plugins written in Python can use
`because` to consume BCS services. It provides a simple QGIS UI that you can
use to interact with the services.


Requirements
------------

To run this plugin, you need to have QGIS installed with support for Python
plugins. The plugin should run with either QGIS 2 (PyQt4, Python 2.7) or QGIS 3
(PyQt5, Python3).


Limitations
-----------

This example plugin is really only to show some examples of how to use
`because` within QGIS plugins written in Python. As a result, it has a number
of major limitations. For example, it has a crude UI, handles authentication
credentials in a simplistic way, and doesn't use Qt's translation facilities.
The mechanism used for loading basemaps does not handle errors well - something
like QuickMapServices would be a better example of how to consume XYZ basemaps.
A real plugin might provide metadata for publication on the QGIS plugin
repository.
