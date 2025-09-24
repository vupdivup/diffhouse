import logging
import sys

from . import constants

logger = logging.getLogger(constants.PACKAGE_NAME)

if not logger.hasHandlers():
    formatter = logging.Formatter(
        f'{constants.PACKAGE_NAME} %(asctime)s.%(msecs)03d %(message)s',
        datefmt='%H:%M:%S')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)