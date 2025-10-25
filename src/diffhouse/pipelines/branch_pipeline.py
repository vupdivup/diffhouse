import logging
import re
from typing import Iterator

from diffhouse.entities import Branch
from diffhouse.git import GitCLI

logger = logging.getLogger(__name__)


def extract_branches(path: str) -> Iterator[Branch]:
    """Get branches of a local git repository.

    Args:
        path: Path to the local git repository.

    Yields:
        Branch objects.

    """
    logger.info('Extracting branches')
    logger.debug('Logging branches')

    log = log_branches(path)

    logger.debug('Parsing branches')

    yield from parse_branches(log)

    logger.debug('Extracted all branches')


def log_branches(path: str) -> str:
    """Return the output of `git ls-remote --heads/--branches` for a local repository.

    Args:
        path (str): Path to the local git repository.

    """
    git = GitCLI(path)
    return git.ls_remote('branches')


def parse_branches(log: str) -> Iterator[Branch]:
    """Parse the output of `log_branches`.

    Args:
        log: The output string from `git ls-remote --heads/--branches`.

    Yields:
        Branch objects.

    """
    for branch in re.findall(r'refs/heads/(.+)\n', log):
        yield Branch(name=branch)
