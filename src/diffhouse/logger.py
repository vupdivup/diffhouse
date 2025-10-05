import logging
import sys
from contextlib import contextmanager

from . import constants

formatter = logging.Formatter(
    f'{constants.PACKAGE_NAME} %(asctime)s.%(msecs)03d %(message)s',
    datefmt='%H:%M:%S',
)

logger = logging.getLogger(constants.PACKAGE_NAME)
logger.setLevel(logging.INFO)

# self-contained logger
logger.propagate = False


@contextmanager
def log_to_stdout(logger, level: int = logging.INFO, enabled: bool = True):
    """Temporarily direct messages of a logger to stdout.

    Args:
        logger: The logger to attach the handler to.
        level: The exact logging level to capture.
        enabled: Whether to enable the temporary logging.

    Raises:
        RuntimeError: If the logger already has handlers attached.

    """
    if enabled:
        if logger.hasHandlers():
            raise RuntimeError('Logger already has handlers attached.')

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        # filter for a single level
        handler.addFilter(lambda record: record.levelno == level)

        logger.addHandler(handler)

    try:
        yield None
    finally:
        if enabled:
            logger.removeHandler(handler)
            handler.close()
