from dataclasses import dataclass
from collections.abc import Iterator

from ..git import GitCLI
from .constants import RECORD_SEPARATOR


@dataclass
class Revision:
    """A file change in a specific commit."""

    commit_hash: str
    """Full hash of the commit."""
    path_a: str
    """Path to file before the commit."""
    path_b: str
    """Path to file after the commit."""
    revision_id: str
    """File revision ID."""
    status: str
    """Single-letter code representing the change type. See [git-status](https://git-scm.com/docs/git-status#_short_format) for possible values."""
    similarity: int
    """Similarity index for renames and copies (0-100)."""

    # TODO: no of lines added/deleted


def collect_revisions(path: str) -> Iterator[Revision]:
    """
    Get file revisions per commit for local repository at `path`.
    """
    log = _log_revisions(path)
    yield from _parse_revisions(log)


def _log_revisions(path: str, sep: str = RECORD_SEPARATOR) -> str:
    """
    Return the output of `git log --name-status` with commits delimited by
    `sep` for local repository at `path`.
    """
    git = GitCLI(path)
    return git.run("log", f"--pretty=format:{sep}%H", "--name-status")


def _parse_revisions(log: str, sep: str = RECORD_SEPARATOR) -> Iterator[Revision]:
    """
    Parse the output of `_log_revisions`.
    """
    commits = log.split(sep)[1:]

    for c in commits:
        lines = c.strip().split("\n")
        hash = lines[0]

        for l in lines[1:]:
            items = l.split("\t")
            status = items[0][0]

            if status in ["R", "C"]:
                similarity = int(items[0][1:])
                path_b = items[2]
                path_a = items[1]
            else:
                similarity = 100
                path_b = items[1]
                path_a = path_b

            yield Revision(
                commit_hash=hash,
                path_a=path_a,
                path_b=path_b,
                revision_id=f"{hash}:{path_b}",
                status=status,
                similarity=similarity,
            )
