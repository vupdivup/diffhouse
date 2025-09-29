import re

from ..git import GitCLI


def collect_tags(path: str) -> list[str]:
    """
    Get tags of a git repository at `path` via `git ls-remote`.
    """
    log = log_tags(path)
    return parse_tags(log)


def log_tags(path: str) -> str:
    """
    Return the output of `git ls-remote --tags` for repository at `path`.
    """
    git = GitCLI(path)
    return git.ls_remote("tags")


def parse_tags(log: str) -> list[str]:
    """
    Parse the output of `log_tags` passed via the `log` argument.
    """
    return re.findall(r"refs/tags/(.+)\n", log)
