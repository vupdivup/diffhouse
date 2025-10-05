import re
from collections.abc import Iterator
from dataclasses import dataclass

from ..git import GitCLI
from .constants import RECORD_SEPARATOR, UNIT_SEPARATOR
from .utils import tweak_git_iso_datetime

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
    files_changed: int | None
    """
    Number of files changed in the commit.

    Available if `blobs` is `True`.
    """
    lines_added: int | None
    """
    Number of lines inserted in the commit.

    Available if `blobs` is `True`.
    """
    lines_deleted: int | None
    """Number of lines deleted in the commit.

    Available if `blobs` is `True`.
    """


def collect_commits(path: str, shortstats: bool = False) -> Iterator[Commit]:
    """Return main branch commit data from a git repository at `path`."""
    log = log_commits(path, shortstats=shortstats)
    yield from parse_commits(log, parse_shortstats=shortstats)


def log_commits(
    path: str,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
    shortstats: bool = False,
) -> str:
    """Return a normalized git log from a local repository.

    Args:
        path (str): The file system path to the local git repository.
        field_sep: Separator between fields in each commit.
        record_sep: Separator between commits.
        shortstats: Whether to include a shortstat summary of changes per commit.

    """
    # prepare git log command
    specifiers = field_sep.join(PRETTY_LOG_FORMAT_SPECIFIERS.values())

    pattern = f'{record_sep}{specifiers}{UNIT_SEPARATOR}'
    args = ['log', f'--pretty=format:{pattern}', '--date=iso']

    if shortstats:
        args.append('--shortstat')

    git = GitCLI(path)
    return git.run(*args)


def parse_commits(
    log: str,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
    parse_shortstats: bool = False,
) -> Iterator[Commit]:
    """Parse the output of `log_commits`."""
    commits = log.split(record_sep)[1:]

    files_changed_pat = re.compile(r'(\d+) file')
    insertions_pat = re.compile(r'(\d+) insertion')
    deletions_pat = re.compile(r'(\d+) deletion')

    for c in commits:
        values = c.split(field_sep)

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
