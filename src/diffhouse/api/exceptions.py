class NotClonedError(Exception):
    """Exception for when resources are requested without a local clone."""

    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__(
            'The repository is not cloned locally.\n'
            'Use the Repo in a with statement or call its clone() method first to access this resource.'
        )


class FilterError(Exception):
    """Exception for disparities between filters and requested data."""

    def __init__(self, filter_name: str) -> None:
        """Initialize the exception.

        Args:
            filter_name: Name of the incompatible filter.

        """
        super().__init__(
            f"Requested data is incompatible with the current '{filter_name}'"
            ' filter.'
        )


class GitError(Exception):
    """Exception for git-related errors."""

    def __init__(self, stderr: str) -> None:
        """Initialize the exception.

        Args:
            stderr: Standard error output from the git command.

        """
        super().__init__(
            f'Git command failed with the following error:\n{stderr}'
        )
