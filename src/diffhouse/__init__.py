import logging.config

from .repo import Repo
from . import config

logging.config.dictConfig(config.LOGGING)

__all__ = ['Repo']
