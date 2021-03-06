because
=======


``because`` is a Python library for using 
:doc:`BCS HTTP services <services>` including 
:doc:`routing <services/routing>`,
:doc:`geocoding <services/geocoding>`,
:doc:`basemaps <services/basemaps>`,
and
:doc:`search <services/search>`.

It wraps these services in high-level interfaces that abstract away
many of the ugly details, so you can get started quickly and focus on how you
want to use the data.


Getting Started
---------------

If you want to dive right in, feel free to check out the 
:doc:`Installation Instructions <installation>` 
and :doc:`Quickstart Tutorial <quickstart>`.

.. note::

    To use Boundless services you will need authentication credentials.
    You can sign up at `Boundless Connect
    <https://connect.boundlessgeo.com/>`_.


Interfaces
----------

Several :doc:`interfaces <interfaces>` are provided, each tailored to a different
environment. For example, there is an interface for plain Python, one for
general use with PyQt, and another tailored for QGIS plugins.


Layered API
-----------

``because`` provides a "layered API": the core, lower-level components used to
make the high-level interfaces are also exposed, for reuse in cases where the
high-level interfaces do not suit your needs.


API Reference
-------------

If you are looking for more technical detail on how ``because`` is put
together, you may be interested in the :doc:`API Reference
<reference/because>`.


.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Contents:

   installation
   quickstart

   interfaces

   services/index
   services

   reference/because


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
