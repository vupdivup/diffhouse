import yaml
import logging
import logging.config
import importlib.resources

from .repo import Repo

with importlib.resources.path('diffhouse', 'logging.yml') as config_path:
    with open(config_path) as f:
        config_path = yaml.safe_load(f)
        logging.config.dictConfig(config_path)

__all__ = ['Repo']
