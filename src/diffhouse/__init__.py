import yaml
import logging
import logging.config
from importlib import resources

from .repo import Repo
from .constants import PACKAGE_NAME

with (resources.files(PACKAGE_NAME) / 'static/logging.yml').open('r') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

__all__ = ['Repo']
