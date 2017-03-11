"""Code and interface definitions for specific services hosted by BCS.

Each subpackage may include such things as:

* Service and Endpoint definitions, or classes for constructing them

* Request generators

* Response parsers

* Data structures representing parsed results in a more usable form

:note: Service descriptions do not hard-code base URLs, which must be provided
separately to produce a complete Request. This allows the same service
definitions to be used across different hosts, and for hosts to be specifiable
e.g. in local config files.
"""
