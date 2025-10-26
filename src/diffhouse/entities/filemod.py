from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class FileMod:
    """A file modification in a specific commit."""

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns:
            A dictionary representation of the file modification.

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
    Unique record identifier hashed from `commit_hash`, `path_a`, and `path_b`.
    """
    change_type: str
    """
    Single-letter code representing the change type.

    Most commonly one of `A` (added), `C` (copied), `D` (deleted), `M`
    (modified) or `R` (renamed). See
    [git-status](https://git-scm.com/docs/git-status#_short_format) for all
    possible values.
    """
    similarity: int
    """
    Similarity index between the two file versions.

    `0`-`100` for renames and copies, `100` otherwise.
    """
    lines_added: int
    """Number of lines added to the file in the commit."""
    lines_deleted: int
    """Number of lines deleted from the file in the commit."""
