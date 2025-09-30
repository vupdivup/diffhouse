import re

from collections.abc import Iterator

from ..git import GitCLI

# TODO: parse line by line


def get_tags(path: str) -> Iterator[str]:
    """
    Get tags of a git repository at `path` via `git ls-remote`.
    """
    log = log_tags(path)
    yield from parse_tags(log)


def log_tags(path: str) -> str:
    """
    Return the output of `git ls-remote --tags` for repository at `path`.
    """
    git = GitCLI(path)
    return git.ls_remote("tags")


def parse_tags(log: str) -> Iterator[str]:
    """
    Parse the output of `log_tags` passed via the `log` argument.
    """
    yield from re.findall(r"refs/tags/(.+)\n", log)
