import re
from typing import Iterator

from diffhouse.entities import Tag
from diffhouse.git import GitCLI


def extract_tags(path: str) -> Iterator[Tag]:
    """Get tags of a local git repository.

    Args:
        path: Path to the local git repository.

    Yields:
        Tag objects.

    """
    log = log_tags(path)
    yield from parse_tags(log)


def log_tags(path: str) -> str:
    """Return the output of `git ls-remote --tags`.

    Args:
        path: Path to the local git repository.

    Returns:
        The output string from `git ls-remote --tags`.

    """
    git = GitCLI(path)
    return git.ls_remote('tags')


def parse_tags(log: str) -> Iterator[str]:
    """Parse the output of `log_tags`.

    Args:
        log: The output string from `git ls-remote --tags`.

    Yields:
        Tag objects.

    """
    for tag in re.findall(r'refs/tags/(.+)\n', log):
        yield Tag(name=tag)
