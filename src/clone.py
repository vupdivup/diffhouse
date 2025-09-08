import tempfile
import subprocess

from pathlib import Path

from .log import Log

class Clone:
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
    def log(self):
        """Commit log of the repository."""
        return self._log

    def __enter__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._path = Path(self._temp_dir.name)

        # run git clone
        subprocess.run([
            'git',
            'clone',
            '--bare',
            '--filter=blob:none',
            self._url,
            self._path
        ])

        # init log
        self._log = Log(self._path)

        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp_dir.cleanup()
