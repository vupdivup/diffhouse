import yaml
import logging
import logging.config
import importlib.resources

from .repo import Repo

with importlib.resources.path('diffhouse', 'logging.yml') as lf:
    with open(lf) as f:
        config = yaml.safe_load(f)
        logging.config.dictConfig(config)

__all__ = ['Repo']
