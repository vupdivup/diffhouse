from collections import namedtuple
from collections.abc import Iterator

from ..git import GitCLI
from .constants import RECORD_SEPARATOR

Revision = namedtuple(
    "Revision", ["commit_hash", "file", "status", "from_file", "similarity"]
)


def collect_revisions(path: str) -> list[Revision]:
    """
    Get file revisions per commit for local repository at `path`.
    """
    log = _log_revisions(path)
    return list(_parse_revisions(log))


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
                similarity = float(items[0][1:])
                file = items[2]
                from_file = items[1]
            else:
                similarity = None
                file = items[1]
                from_file = None

            yield Revision(
                commit_hash=hash,
                file=file,
                status=status,
                from_file=from_file,
                similarity=similarity,
            )
