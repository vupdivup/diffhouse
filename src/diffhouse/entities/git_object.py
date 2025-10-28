from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class GitObject:
    """Base class for Git entities."""

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns:
            A dictionary representation of the Git object.

        """
        return asdict(self)
