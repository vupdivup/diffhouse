from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class Branch:
    """A branch in the repository."""

    def asdict(self) -> dict:
        """Convert the object to a dictionary.

        Returns:
            A dictionary representation of the branch.

        """
        return asdict(self)

    name: str
    """Name of the branch."""
