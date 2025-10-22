from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class Tag:
    """A tag in the repository."""

    def asdict(self) -> dict:
        """Convert the object to a dictionary.

        Returns:
            A dictionary representation of the tag.

        """
        return asdict(self)

    name: str
    """Name of the tag."""
