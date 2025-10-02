import re
from collections.abc import Iterator
from dataclasses import dataclass

from ..git import GitCLI
from .constants import RECORD_SEPARATOR, UNIT_SEPARATOR

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


# TODO: shortstat
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
    """Original commit date in ISO 8601 format, with timezone offset."""
    committer_name: str
    """Committer name."""
    committer_email: str
    """Committer email."""
    committer_date: str
    """Actual commit date in ISO 8601 format, with timezone offset."""
    subject: str
    """Commit message subject."""
    body: str
    """Commit message body."""
    files_changed: int
    """Number of files changed in the commit."""
    insertions: int
    """Number of lines inserted in the commit."""
    deletions: int
    """Number of lines deleted in the commit."""


def collect_commits(path: str) -> Iterator[Commit]:
    """Return main branch commit data from a git repository at `path`."""
    log = log_commits(path)
    yield from parse_commits(log)


def log_commits(
    path: str,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
) -> str:
    """Return a normalized git log from repository at `path` with custom formatting.

    Commits are separated by `record_sep` and fields within each commit are
    separated by `field_sep`.
    """
    # prepare git log command
    specifiers = field_sep.join(PRETTY_LOG_FORMAT_SPECIFIERS.values())

    pattern = f'{record_sep}{specifiers}{UNIT_SEPARATOR}'

    git = GitCLI(path)
    return git.run(
        'log', f'--pretty=format:{pattern}', '--date=iso', '--shortstat'
    )


def parse_commits(
    log: str,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
) -> Iterator[Commit]:
    """Parse the output of `log_commits`."""
    commits = log.split(record_sep)[1:]

    shortstat_pat = re.compile(
        r'(?P<files_changed>\d+) file.*'
        r'(?:(?P<insertions>\d+) insertion).*'
        r'(?:(?P<deletions>\d+) deletion)?'
    )

    for c in commits:
        values = c.split(field_sep)

        # match all fields with field names except the shortstat section
        fields = {k: v for k, v in zip(FIELDS, values[:-1])}

        shortstat = values[-1]
        shortstat_match = shortstat_pat.search(shortstat)
        shortstat_dict = shortstat_match.groupdict() if shortstat_match else {}

        if shortstat_match:
            files_changed = int(shortstat_dict.get('files_changed'))
            insertions = int(shortstat_dict.get('insertions', 0) or 0)
            deletions = int(shortstat_dict.get('deletions', 0) or 0)
        else:
            files_changed = 0
            insertions = 0
            deletions = 0

        yield Commit(
            commit_hash=fields['commit_hash'],
            author_name=fields['author_name'],
            author_email=fields['author_email'],
            author_date=fields['author_date'],
            committer_name=fields['committer_name'],
            committer_email=fields['committer_email'],
            committer_date=fields['committer_date'],
            subject=fields['subject'].strip(),
            body=fields['body'].strip(),
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
        )
