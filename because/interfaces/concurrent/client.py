from concurrent import futures

from because.client import Client as _Client
from because.interfaces.python.ssl_config import SSLConfig
from . transfer import Transfer


class Client(_Client):
    ssl_config_cls = SSLConfig
    transfer_cls = Transfer

    def __init__(self, ssl_config=None, log=None):
        self._executor = futures.ThreadPoolExecutor()
        # self._executor = futures.ProcessPoolExecutor()

        super(Client, self).__init__(
            ssl_config=ssl_config,
            log=log,
        )

        assert isinstance(self.ssl_config, SSLConfig)

    def transfer(self, request, log=None):
        return self.transfer_cls(
            request=request,
            log=log,
            _executor=self._executor,
        )
