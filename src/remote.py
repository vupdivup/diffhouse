from .clone import Clone

class Remote:
    """
    GitHub repository metadata.
    """
    def __init__(self, owner: str, name: str):
        """
        Initialize remote via GitHub owner and repository name.
        Args:
            owner (str): Repository owner.
            name (str): Repository name.
        """
        self._owner = owner
        self._name = name
        self._url = f'https://github.com/{owner}/{name}.git'
        self._id = f'{owner}-{name}'

    @property
    def owner(self):
        """Repository owner."""
        return self._owner

    @property
    def name(self):
        """Repository name."""
        return self._name
    
    @property
    def url(self):
        """GitHub repository URL."""
        return self._url
    
    @property
    def id(self):
        """Unique identifier for the repository. Format: `{owner}-{name}`"""
        return self._id

    def clone(self):
        """
        Create a local clone of the repository.
        """
        return Clone(self.url)
