from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class Diff:
    """Changes made to a hunk of code in a specific commit."""

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns:
            A dictionary representation of the diff.

        """
        return asdict(self)

    commit_hash: str
    """Full hash of the commit."""
    path_a: str
    """Path to the file before applying the commit's changes."""
    path_b: str
    """
    Path to the file after applying the commit's changes.

    Differs from `path_a` for renames and copies.
    """
    filemod_id: str
    """
    Hash of `commit_hash`, `path_a`, and `path_b`.

    Use it to match with a `FileMod`.
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
