"""Transfer implementation for QGIS.
"""
import logging
from .. qt.transfer import Transfer as _Transfer


#: Default logger for this module.
LOG = logging.getLogger(__name__)


class Transfer(_Transfer):
    """
    """

    #: Default logger for this class.
    log = LOG.getChild("Transfer")

    # TODO: former args:
    # on_finished=None,
    # on_progress=None,
    # timeout=None,
    # send=None,

    def __init__(
            self,
            request,
            log=None,
            parent=None,
    ):
        """
        :arg request:
        :arg log:
        :arg log:
            Optional. Logger to use.
        :arg parent:
        """
        self.request = request
        self.log = log or self.log

        super(Transfer, self).__init__(
            log=self.log,
            parent=parent,
        )
