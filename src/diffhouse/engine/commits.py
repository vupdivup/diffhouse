import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO

from ..git import GitCLI
from .constants import RECORD_SEPARATOR, UNIT_SEPARATOR
from .utils import safe_iter, split_stream, tweak_git_iso_datetime

PRETTY_LOG_FORMAT_SPECIFIERS = {
    'commit_hash': '%H',
    'author_name': '%an',
    'author_email': '%ae',
    'author_date': '%ad',
    'committer_name': '%cn',
    'committer_email': '%ce',
    'committer_date': '%cd',
    'subject': '%s',
    'body': '%b',
}

FIELDS = list(PRETTY_LOG_FORMAT_SPECIFIERS.keys())


@dataclass
class Commit:
    """Commit metadata."""

    commit_hash: str
    """Full hash of the commit."""
    author_name: str
    """Author name."""
    author_email: str
    """Author email."""
    author_date: str
    """Original commit date and time.

    Adheres to the ISO 8601 datetime format (*YYYY-MM-DDTHH:MM:SS±HH:MM*)."""
    committer_name: str
    """Committer name."""
    committer_email: str
    """Committer email."""
    committer_date: str
    """Actual commit date and time.

    Adheres to the ISO 8601 datetime format (*YYYY-MM-DDTHH:MM:SS±HH:MM*)."""
    subject: str
    """Commit message subject."""
    body: str
    """Commit message body."""
    files_changed: int | None
    """
    Number of files changed in the commit.

    Available if `blobs = True`.
    """
    lines_added: int | None
    """
    Number of lines inserted in the commit.

    Available if `blobs = True`.
    """
    lines_deleted: int | None
    """Number of lines deleted in the commit.

    Available if `blobs = True`.
    """


def stream_commits(path: str, shortstats: bool = False) -> Iterator[Commit]:
    """Stream main branch commits from a git repository.

    Args:
        path: Path to the git repository.
        shortstats: Whether to include shortstat information.

    Yields:
        Commit objects.

    """
    with log_commits(path, shortstats=shortstats) as log:
        yield from safe_iter(
            parse_commits(log, parse_shortstats=shortstats),
            'Failed to parse commit. Skipping...',
        )


@contextmanager
def log_commits(
    path: str,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
    shortstats: bool = False,
) -> Iterator[StringIO]:
    """Return a structured git log as a string stream.

    Args:
        path: Path to the git repository.
        field_sep: Separator between fields in each commit.
        record_sep: Separator between commits.
        shortstats: Whether to include a shortstat summary of changes per
            commit.

    Yields:
        A string stream containing the git log.

    """
    # prepare git log command
    specifiers = field_sep.join(PRETTY_LOG_FORMAT_SPECIFIERS.values())

    pattern = f'{record_sep}{specifiers}{UNIT_SEPARATOR}'
    args = ['log', f'--pretty=format:{pattern}', '--date=iso']

    if shortstats:
        args.append('--shortstat')

    git = GitCLI(path)
    with git.run(*args) as log:
        try:
            yield log
        finally:
            log.close()


def parse_commits(
    log: StringIO,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
    parse_shortstats: bool = False,
) -> Iterator[Commit]:
    """Parse the output of `log_commits`."""
    files_changed_pat = re.compile(r'(\d+) file')
    insertions_pat = re.compile(r'(\d+) insertion')
    deletions_pat = re.compile(r'(\d+) deletion')

    commits = split_stream(log, record_sep, chunk_size=10_000)
    next(commits)  # skip first empty record

    for commit in commits:
        values = commit.split(field_sep)

        # match all fields with field names except the shortstat section
        fields = {k: v for k, v in zip(FIELDS, values[:-1])}

        if parse_shortstats:
            shortstat = values[-1]

            files_changed_match = files_changed_pat.search(shortstat)
            insertions_match = insertions_pat.search(shortstat)
            deletions_match = deletions_pat.search(shortstat)

            files_changed = (
                int(files_changed_match.group(1)) if files_changed_match else 0
            )

            insertions = (
                int(insertions_match.group(1)) if insertions_match else 0
            )
            deletions = int(deletions_match.group(1)) if deletions_match else 0

        else:
            files_changed = None
            insertions = None
            deletions = None

        yield Commit(
            commit_hash=fields['commit_hash'],
            author_name=fields['author_name'],
            author_email=fields['author_email'],
            author_date=tweak_git_iso_datetime(fields['author_date']),
            committer_name=fields['committer_name'],
            committer_email=fields['committer_email'],
            committer_date=tweak_git_iso_datetime(fields['committer_date']),
            subject=fields['subject'].strip(),
            body=fields['body'].strip(),
            files_changed=files_changed,
            lines_added=insertions,
            lines_deleted=deletions,
        )
