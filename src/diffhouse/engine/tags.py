import re

from ..git import GitCLI


def get_tags(path: str) -> list[str]:
    """Get tags of a local git repository.

    Args:
        path: Path to the local git repository.

    Returns:
        A list of tag names.

    """
    log = log_tags(path)
    return parse_tags(log)


def log_tags(path: str) -> str:
    """Return the output of `git ls-remote --tags`.

    Args:
        path: Path to the local git repository.

    Returns:
        The output string from `git ls-remote --tags`.

    """
    git = GitCLI(path)
    return git.ls_remote('tags')


def parse_tags(log: str) -> list[str]:
    """Parse the output of `log_tags`.

    Args:
        log: The output string from `git ls-remote --tags`.

    Returns:
        A list of tag names.

    """
    return re.findall(r'refs/tags/(.+)\n', log)
