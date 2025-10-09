import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO

from ..git import GitCLI
from .constants import RECORD_SEPARATOR
from .utils import hash, safe_iter, split_stream

# TODO: binary diffs


@dataclass
class Diff:
    """Changes made to a hunk of code in a specific commit."""

    commit_hash: str
    """Full hash of the commit."""
    path_a: str
    """Path to the file before applying the commit's changes."""
    path_b: str
    """
    Path to the file after applying the commit's changes.

    Differs from `path_a` for renames and copies.
    """
    changed_file_id: str
    """
    Hash of `commit_hash`, `path_a`, and `path_b`.

    Use it to match with a `ChangedFile`.
    """
    start_a: int
    """Line number that starts the hunk in file version A."""
    length_a: int
    """Line count of the hunk in file version A."""
    start_b: int
    """Line number that starts the hunk in file version B."""
    length_b: int
    """Line count of the hunk in file version B."""
    lines_added: int
    """Number of lines added."""
    lines_deleted: int
    """Number of lines deleted."""
    additions: list[str]
    """Text content of added lines."""
    deletions: list[str]
    """Text content of deleted lines."""


def stream_diffs(path: str) -> Iterator[Diff]:
    """Stream diffs per commit and file for a local repository.

    Args:
        path: Path to the local git repository.

    Yields:
        Diff objects.

    """
    with log_diffs(path) as log:
        yield from safe_iter(
            parse_diffs(log), 'Failed to parse diff. Skipping...'
        )


@contextmanager
def log_diffs(path: str, sep: str = RECORD_SEPARATOR) -> Iterator[StringIO]:
    """Run a variation of `git log -p` and return the output as a string stream.

    Args:
        path: Path to the local repository.
        sep: Separator between commits.

    Yields:
        A string stream containing the git log with diffs.

    """
    git = GitCLI(path)
    with git.run('log', '-p', '-U0', f'--pretty=format:{sep}%H') as log:
        try:
            yield log
        finally:
            log.close()


def parse_diffs(log: StringIO, sep: str = RECORD_SEPARATOR) -> Iterator[Diff]:
    """Parse the output of `log_diffs`.

    Args:
        log: A string stream containing the git log with diffs.
        sep: Separator between commits.

    Yields:
        Diff objects.

    """
    file_sep_pat = re.compile(r'^diff --git', flags=re.MULTILINE)
    filepaths_pat = re.compile(r'"?a/(.+)"? "?b/(.+)"?')
    hunk_header_pat = re.compile(
        r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', flags=re.MULTILINE
    )

    commits = split_stream(log, sep, chunk_size=100_000)
    next(commits)  # skip first empty record

    # note: need big chunk size as diffs can be large
    for commit in commits:
        parts = commit.split('\n', 1)

        commit_hash = parts[0]

        # ignore empty commits
        if len(parts) == 1:
            continue

        files = re.split(file_sep_pat, parts[1])[1:]
        for file in files:
            # format: a/path b/path
            header = file.split('\n', 1)[0]

            path_a, path_b = re.search(filepaths_pat, header).groups()
            hunks_raw = re.split(hunk_header_pat, file)[1:]

            # zip hunk header data with content
            hunks_grouped = tuple(
                {
                    'start_a': int(hunks_raw[i]),
                    'length_a': int(hunks_raw[i + 1] or 1),
                    'start_b': int(hunks_raw[i + 2]),
                    'length_b': int(hunks_raw[i + 3] or 1),
                    'content': hunks_raw[i + 4].split('\n', 1)[1],
                }
                for i in range(0, len(hunks_raw), 5)
            )

            for hunk in hunks_grouped:
                lines = hunk['content'].splitlines()

                lines_added = 0
                lines_deleted = 0
                additions = []
                deletions = []

                for line in lines:
                    if line.startswith('+'):
                        additions.append(line[1:])
                        lines_added += 1
                    elif line.startswith('-'):
                        deletions.append(line[1:])
                        lines_deleted += 1

                yield Diff(
                    commit_hash=commit_hash,
                    path_a=path_a,
                    path_b=path_b,
                    changed_file_id=hash(commit_hash, path_a, path_b),
                    start_a=hunk['start_a'],
                    length_a=hunk['length_a'],
                    start_b=hunk['start_b'],
                    length_b=hunk['length_b'],
                    lines_added=lines_added,
                    lines_deleted=lines_deleted,
                    additions=additions,
                    deletions=deletions,
                )
