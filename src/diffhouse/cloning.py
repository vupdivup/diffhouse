import tempfile
from pathlib import Path

from .git import GitCLI


class TempClone:
    """Local clone of a git repository that resides in a temporary directory.

    For proper cleanup, the class is implemented as a context manager and meant
    to be used in a `with` statement.
    """

    def __init__(self, url: str, shallow: bool):
        """Create a local clone of a remote repository at `url`.

        If `shallow` is `True`, append arguments `--bare` and
        `--filter=blob:none` to the `git clone` command.
        """
        self._url = url
        self._shallow = shallow

    @property
    def path(self):
        """Path to the local clone. Points to a temporary directory."""
        return self._path

    def __enter__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._path = Path(self._temp_dir.name)

        # clone repository
        git = GitCLI(self._path)

        # prepare git clone command
        args = ['clone']

        if self._shallow:
            args.extend(['--bare', '--filter=blob:none'])

        args.extend([self._url, '.'])

        git.run(*args)

        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self._temp_dir.cleanup()
