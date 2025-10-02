from collections.abc import Iterator
from dataclasses import dataclass

from ..git import GitCLI
from .constants import RECORD_SEPARATOR
from .utils import hash


@dataclass
class ChangedFile:
    """Snapshot of a file that was modified in a specific commit."""

    commit_hash: str
    """Full hash of the commit."""
    path_a: str
    """Path to file before the commit."""
    path_b: str
    """
    Path to file after the commit.
    
    Differs from `path_a` for renames and copies.
    """
    changed_file_id: str
    """
    Unique record identifier hashed from `commit_hash`, `path_a`, and `path_b`.
    """
    change_type: str
    """
    Single-letter code representing the change type. 
    
    See [git-status](https://git-scm.com/docs/git-status#_short_format) for
    possible values.
    """
    similarity: int
    """
    Similarity index between the two file versions.
    
    `0`-`100` for renames and copies, `100` otherwise.
    """

    # TODO: no of lines added/deleted


def collect_changed_files(path: str) -> Iterator[ChangedFile]:
    """Get changed files per commit for local repository at `path`."""
    log = _log_changed_files(path)
    yield from _parse_changed_files(log)


def _log_changed_files(path: str, sep: str = RECORD_SEPARATOR) -> str:
    """Return the output of `git log --name-status` for a local repository.

    Args:
        path (str): Path to the local git repository.
        sep (str): Record separator between commits.

    """
    git = GitCLI(path)
    return git.run('log', f'--pretty=format:{sep}%H', '--name-status')


def _parse_changed_files(
    log: str, sep: str = RECORD_SEPARATOR
) -> Iterator[ChangedFile]:
    """Parse the output of `_log_changed_files`."""
    commits = log.split(sep)[1:]

    for c in commits:
        lines = c.strip().split('\n')
        commit_hash = lines[0]

        for line in lines[1:]:
            items = line.split('\t')
            change_type = items[0][0]

            if change_type in ['R', 'C']:
                similarity = int(items[0][1:])
                path_b = items[2]
                path_a = items[1]
            else:
                similarity = 100
                path_b = items[1]
                path_a = path_b

            yield ChangedFile(
                commit_hash=commit_hash,
                path_a=path_a,
                path_b=path_b,
                changed_file_id=hash(commit_hash, path_a, path_b),
                change_type=change_type,
                similarity=similarity,
            )
