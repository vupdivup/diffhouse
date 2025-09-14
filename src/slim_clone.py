import tempfile

from pathlib import Path

from .git import GitCLI

class SlimClone:
    """
    Local bare clone of a git repository.
    
    Resides in a temporary directory. For proper cleanup, the class is
    implemented as a context manager and meant to be used in a `with` statement.
    """
    def __init__(self, url: str):
        """
        Create a local clone of a remote repository.

        Args:
            url (str): URL of the remote repository.
        """
        self._url = url

    @property
    def path(self):
        """Path to the local clone. Points to a temporary directory."""
        return self._path

    def __enter__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._path = Path(self._temp_dir.name)

        # clone repository
        git = GitCLI(self._path)
        git.run(
            'clone', '--bare', '--filter=blob:none', self._url, '.'
        )

        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp_dir.cleanup()
