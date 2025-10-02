import re

from collections.abc import Iterator

from ..git import GitCLI


def get_branches(path: str) -> Iterator[str]:
    """
    Get branches of a git repository at `path` via git `ls-remote`.
    """
    log = log_branches(path)
    yield from parse_branches(log)


def log_branches(path: str) -> str:
    """
    Return the output of `git ls-remote --heads/--branches` for branches of the
    repository at `path`.
    """
    git = GitCLI(path)
    return git.ls_remote("branches")


def parse_branches(log: str) -> Iterator[str]:
    """
    Parse the output of `log_branches` passed via the `log` argument.
    """
    yield from re.findall(r"refs/heads/(.+)\n", log)
