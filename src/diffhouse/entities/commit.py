from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class Commit:
    """A commit from the repository history."""

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns:
            A dictionary representation of the commit.

        """
        return asdict(self)

    commit_hash: str
    """Full hash of the commit."""
    date: datetime
    """Date and time when the commit was applied, in UTC."""
    date_local: datetime
    """Date and time when the commit was applied, in local time."""
    message_subject: str
    """Commit message subject."""
    message_body: str
    """Commit message body."""
    author_name: str
    """Author name."""
    author_email: str
    """Author email."""
    author_date: datetime
    """Date and time when the commit was authored, in UTC."""
    author_date_local: datetime
    """Date and time when the commit was authored, in local time."""
    committer_name: str
    """Committer name."""
    committer_email: str
    """Committer email."""
    files_changed: int | None
    """
    Number of files changed in the commit.

    The value of this attribute equals `None` if `blobs=False`.
    """
    lines_added: int | None
    """
    Number of lines inserted in the commit.

    The value of this attribute equals `None` if `blobs=False`.
    """
    lines_deleted: int | None
    """Number of lines deleted in the commit.

    The value of this attribute equals `None` if `blobs=False`.
    """
    source: str
    """The original branch that produced the commit."""
    in_main: bool
    """Whether the commit is in the default branch's history."""
    is_merge: bool
    """Whether the commit is a merge commit."""
    parents: list[str]
    """List of parent commit hashes."""
