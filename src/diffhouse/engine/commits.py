from dataclasses import dataclass
from collections.abc import Iterator

from ..git import GitCLI
from .constants import RECORD_SEPARATOR, UNIT_SEPARATOR

PRETTY_LOG_FORMAT_SPECIFIERS = {
    "commit_hash": "%H",
    "author_name": "%an",
    "author_email": "%ae",
    "author_date": "%ad",
    "committer_name": "%cn",
    "committer_email": "%ce",
    "committer_date": "%cd",
    "subject": "%s",
    "body": "%b",
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
    """Date when the author made the commit."""
    committer_name: str
    """Committer name."""
    committer_email: str
    """Committer email."""
    committer_date: str
    """Date when the committer committed the change."""
    subject: str
    """Commit message subject."""
    body: str
    """Commit message body."""


def collect_commits(path: str) -> Iterator[Commit]:
    """Return main branch commit data from a git repository at `path`."""
    log = log_commits(path)
    yield from parse_commits(log)


def log_commits(
    path: str, field_sep: str = UNIT_SEPARATOR, record_sep: str = RECORD_SEPARATOR
) -> str:
    """Return a normalized git log from repository at `path` with custom formatting.

    Commits are separated by `record_sep` and fields within each commit are separated by
    `field_sep`.
    """
    # prepare git log command
    specifiers = field_sep.join(PRETTY_LOG_FORMAT_SPECIFIERS.values())

    pattern = f"{record_sep}{specifiers}"

    git = GitCLI(path)
    return git.run("log", f"--pretty=format:{pattern}", "--date=iso")


def parse_commits(
    log: str, field_sep: str = UNIT_SEPARATOR, record_sep: str = RECORD_SEPARATOR
) -> Iterator[Commit]:
    """Parse the output of `log_commits`."""
    commits = log.split(record_sep)[1:]

    for c in commits:
        fields = {k: v for k, v in zip(FIELDS, c.split(field_sep))}

        yield Commit(
            commit_hash=fields["commit_hash"],
            author_name=fields["author_name"],
            author_email=fields["author_email"],
            author_date=fields["author_date"],
            committer_name=fields["committer_name"],
            committer_email=fields["committer_email"],
            committer_date=fields["committer_date"],
            subject=fields["subject"].strip(),
            body=fields["body"].strip(),
        )
