=================
Geocoding Service
=================

The geocoding service lets you convert between WGS84 latitude/longitude
coordinates and textual addresses. Forward geocoding is address to location
(lat/lon), and reverse geocoding is location (lat/lon) to address.

The service returns multiple matches, each with an estimate of how relevant it
might be, so that you can decide for yourself what to do with ambiguous cases.
you can also choose which source you would like the geocoding data to come
from, like Mapbox or Mapzen.


Examples
--------

The following simple example logs in to BCS, requests candidate locations for
the address with data from Mapbox, then prints each of the candidate locations.

.. code-block:: python

    from because import Because

    bcs = Because()
    username = "myusername"
    password = "mypassword"
    bcs.login(username, password).wait()

    address = "1600 Pennsylvania Ave., Washington, DC"
    matches = bcs.geocode(address, service="mapbox").wait()
    for index, match in enumerate(matches):
        print("Match {}:".format(index))
        print(
            """
            Score: {}
            Location: ({}, {})
            Address: {}
            """.format(match.score, match.x,  match.y, match.address),
        )


Here is an example of reverse geocoding, where a location is given and
addresses are returned.

.. code-block:: python

    from because import Because

    bcs = Because()
    username = "myusername"
    password = "mypassword"
    bcs.login(username, password).wait()

    x, y = (-76.981041, 38.878649)
    matches = bcs.reverse_geocode(x, y, service="mapbox").wait()
    for index, match in enumerate(matches):
        print("Match {}:".format(index))
        print(
            """
            Score: {}
            Location: ({}, {})
            Address: {}
            """.format(match.score, match.x,  match.y, match.address)
        )


API Reference
-------------

.. toctree::
   :maxdepth: 3

   ../reference/because.services.geocoding
