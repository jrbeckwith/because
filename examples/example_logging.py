import logging


def configure_logging(debug=False):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.WARNING,
    )
    logger = logging.getLogger("Because")
    return logger
