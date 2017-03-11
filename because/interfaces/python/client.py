"""Hold parameters and state for making any number of HTTP requests.
"""
from because.client import Client as _Client
from . ssl_config import SSLConfig
from . transfer import Transfer



class Client(_Client):
    """Make HTTP requests according to a specified policy.
    """
    # Just drop in the Python stdlib implementations
    ssl_config_cls = SSLConfig
    transfer_cls = Transfer
