import re

from ..git import GitCLI


def collect_branches(path: str) -> list[str]:
    """
    Get branches of a git repository at `path` via `git ls-remote`.
    """
    log = log_branches(path)
    return parse_branches(log)


def log_branches(path: str) -> str:
    """
    Return the output of `git ls-remote --heads/--branches` for branches of the
    repository at `path`.
    """
    git = GitCLI(path)
    return git.ls_remote("branches")


def parse_branches(log: str) -> list[str]:
    """
    Parse the output of `log_branches` passed via the `log` argument.
    """
    branches = re.findall(r"refs/heads/(.+)\n", log)
    return branches
