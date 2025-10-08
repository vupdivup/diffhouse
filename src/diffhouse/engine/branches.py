import re

from ..git import GitCLI


def get_branches(path: str) -> list[str]:
    """Get branches of a local git repository.

    Args:
        path: Path to the local git repository.

    Returns:
        A list of branch names.

    """
    log = log_branches(path)
    return parse_branches(log)


def log_branches(path: str) -> str:
    """Return the output of `git ls-remote --heads/--branches` for a local repository.

    Args:
        path (str): Path to the local git repository.

    """
    git = GitCLI(path)
    return git.ls_remote('branches')


def parse_branches(log: str) -> list[str]:
    """Parse the output of `log_branches`.

    Args:
        log: The output string from `git ls-remote --heads/--branches`.

    Returns:
        A list of branch names.

    """
    return re.findall(r'refs/heads/(.+)\n', log)
