"""Define locations and metadata for hosts running public BCS services.

This module contains only a dictionary called HOSTS. Each key is a short alias
for a host giving its role, e.g. "dev", "test", or "prod". Each value is an
instance of boundless.service.Host, containing a base URL and any
associated information necessary to use it, aside from information about
services and endpoints.
"""
from . service import Host

#:
HOSTS = {
    "dev": Host("https://saasy.boundlessgeo.io"),
    "test": Host("https://saasy.boundlessgeo.io"),
    "prod": Host("https://saasy.boundlessgeo.io"),

    #: This host can be used for debug if you locally run some debug HTTP
    #: server on port 8000, handy for testing without hitting real BCS.
    "local": Host("http://localhost:8000/v1"),
}


__all__ = ["HOSTS"]
