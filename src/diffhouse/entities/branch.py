from dataclasses import dataclass

from diffhouse.entities.git_object import GitObject


@dataclass(slots=True, frozen=True)
class Branch(GitObject):
    """A branch in the repository."""

    name: str
    """Name of the branch."""
