import yaml
import logging
import logging.config
from importlib import resources

from .repo import Repo

PACKAGE_NAME = 'diffhouse'

with (resources.files('diffhouse') / 'static/logging.yml').open('r') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

__all__ = ['Repo']
