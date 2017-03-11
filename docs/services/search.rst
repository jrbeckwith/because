==============
Search Service
==============

The search service provides a way to search for content on Boundless Connect.

Many of the details of this service are still being worked out, so stay tuned.

Examples
--------

Here's how to enumerate content categories.

.. code-block:: python

    from because import Because
    bcs = Because()
    username = "myusername"
    password = "mypassword"
    bcs.login(username, password).wait()
    categories = because.search_categories().wait()
    for key, category in categories.items():
        print("Category {}: {}".format(category.key, category.description))

Here's how to search for documents (DOC category) about GeoServer.

.. code-block:: python

    from because import Because
    bcs = Because()
    username = "myusername"
    password = "mypassword"
    bcs.login(username, password).wait()

    results = because.search_category("DOC", "geoserver").wait()
    for index, result in enumerate(results, 1):
        print("Result {}: {}".format(index, result.title))
        print("    {}".format(result.url))
        print()

Here's how to use the opensearch endpoint, which is just a different way of
getting search results.

.. code-block:: python

    from because import Because
    bcs = Because()
    username = "myusername"
    password = "mypassword"
    bcs.login(username, password).wait()

    results = because.opensearch("geoserver").wait()
    for index, result in enumerate(results, 1):
        print("Result {}: {}".format(index, result.title))
        print("    {}".format(result.url))
        print()


API Reference
-------------

.. toctree::
   :maxdepth: 3

   ../reference/because.services.search
