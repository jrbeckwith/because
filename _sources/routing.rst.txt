===============
Routing Service
===============

The routing service lets you get routes which tell how to get from one place to
another, with vector data and step-by-step instructions. 

You can specify just an origin location and a destination location, or you can
specify several waypoints to travel through. You can specify each location
either with latitude and longitude, or with addresses. You can also choose
which source you would like the route data to come from, like Mapbox or Mapzen. 


Example
-------

The following simple example logs in to BCS, then finds a route between two
addresses, getting the data from Mapbox. Once it has a route, it iterates over
its legs; for each leg, it iterates over its steps; and for each step, it
prints out the instructions for that step, and the accompanying list of points
representing the path taken when taking that step.

.. code-block:: python

    from because import Because

    bcs = Because()
    username = "myusername"
    password = "mypassword"
    bcs.login(username, password).wait()

    home = "3637 Far West Blvd, Austin, TX 78731"
    dest = "1600 Pennsylvania Ave., Washington, DC"
    route = bcs.route(home, dest, service="mapbox").wait()

    for leg_number, leg in enumerate(route.legs()):
        print("Leg {}:".format(leg_number))
        for step_number, step in enumerate(leg.steps()):
            print("Step {}:".format(step_number))
            print(step.instructions)
            print(step.points)


API Reference
-------------

.. toctree::
   :maxdepth: 3

   ../reference/because.services.routing
