"""Interfaces for using because in different environments.
"""
from typing import (
    Any,
)
# Don't just pass through strings to importlib for security reasons.
from because.interfaces.python.client import Client as PythonClient


#: Enumerate usable interfaces (Client implementations).
INTERFACES = {}  # type: dict[str, Any]
INTERFACES["python"] = PythonClient

try:
    from because.interfaces.concurrent.client import Client as ConcurrentClient
    INTERFACES["concurrent"] = ConcurrentClient
except ImportError:
    pass

try:
    from because.interfaces.qt.client import Client as QtClient
    INTERFACES["qt"] = QtClient
except ImportError:
    pass
try:
    from because.interfaces.qgis.client import Client as QGISClient
    INTERFACES["qgis"] = QGISClient
except ImportError:
    pass

__all__ = ["INTERFACES"]
