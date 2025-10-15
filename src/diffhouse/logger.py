import logging
import sys
import warnings
from contextlib import contextmanager

from . import constants

formatter = logging.Formatter(
    f'{constants.PACKAGE_NAME} %(asctime)s.%(msecs)03d %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)

package_logger = logging.getLogger(constants.PACKAGE_NAME)
package_logger.setLevel(logging.INFO)

# the package logger is meant for:
# 1. debugging during local development
# 2. printing to stdout when `verbose=True`
# but not for user-configured logging, so we disable propagation
package_logger.propagate = False


@contextmanager
def log_to_stdout(logger, level: int = logging.INFO, enabled: bool = True):
    """Temporarily direct messages of a logger to stdout.

    Args:
        logger: The logger to attach the handler to.
        level: The minimum logging level to capture.
        enabled: Whether to enable the temporary logging.

    """
    apply = enabled and not logger.hasHandlers()  # TODO: has stream handlers

    if enabled and not apply:
        warnings.warn('Logger already has handlers attached. Skipping...')

    if apply:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        handler.setLevel(level)

        logger.addHandler(handler)

    try:
        yield None
    finally:
        if apply:
            logger.removeHandler(handler)
            handler.close()
