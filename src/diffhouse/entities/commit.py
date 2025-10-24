from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class Commit:
    """Commit metadata."""

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns:
            A dictionary representation of the commit.

        """
        return asdict(self)

    commit_hash: str
    """Full hash of the commit."""
    source: str
    """The original branch that produced the commit."""
    in_main: bool
    """Whether the commit is in the default branch's history."""
    is_merge: bool
    """Whether the commit is a merge commit."""
    parents: list[str]
    """List of parent commit hashes."""
    author_name: str
    """Author name."""
    author_email: str
    """Author email."""
    author_date: str
    """Original commit date and time.

    Formatted as an ISO 8601 datetime string (*YYYY-MM-DDTHH:MM:SS±HH:MM*)."""
    committer_name: str
    """Committer name."""
    committer_email: str
    """Committer email."""
    committer_date: str
    """Actual commit date and time.

    Formatted as an ISO 8601 datetime string (*YYYY-MM-DDTHH:MM:SS±HH:MM*)."""
    message_subject: str
    """Commit message subject."""
    message_body: str
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
