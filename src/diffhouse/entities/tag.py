from dataclasses import dataclass

from diffhouse.entities.git_object import GitObject


@dataclass(slots=True, frozen=True)
class Tag(GitObject):
    """A tag in the repository."""

    name: str
    """Name of the tag."""
