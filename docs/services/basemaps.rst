================
Basemaps Service
================

The basemaps service offers a set of basemap rasters in an XYZ format (the same
type as Google, Bing, or OSM maps) suitable for web maps or in QGIS.

You can ask because for a list of the basemaps offered, so that you can get XYZ
endpoints.

To use a basemap, the client may need to send an Authorization header or else
append an API key to the URL. Right now you would have to talk to someone like
Tom to get one of these. Stay tuned.

Examples
--------

.. code-block:: python

    from because import Because

    bcs = Because()
    username = "myusername"
    password = "mypassword"
    bcs.login(username, password).wait()

    basemaps = bcs.basemaps().wait()
    for basemap in basemaps:
        print("Basemap {}: {}".format(basemap.title, basemap.url))


.. TODO: QGIS example with the provided QgsRasterLayer thing I made
.. TODO: JS example with I guess WebSDK


API Reference
-------------

.. toctree::
   :maxdepth: 3

   ../reference/because.services.basemaps
