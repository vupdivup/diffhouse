from collections.abc import Iterator

from .logger import logger
from .cloning import TempClone
from .engine import (
    Commit,
    Revision,
    Diff,
    collect_commits,
    collect_revisions,
    collect_diffs,
    get_branches,
    get_tags,
)


class Repo:
    """
    Represents a git repository.
    """

    # TODO: verbose
    def __init__(self, url: str, blobs: bool = False):
        """
        Initialize the repository from remote at `url`.
        """
        self._blobs = blobs
        self._url = url.strip()
        self._active = False

    def __enter__(self):
        self._clone = TempClone(self.url, shallow=not self._blobs)
        self._clone.__enter__()
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._clone.__exit__(exc_type, exc_value, traceback)
        self._active = False

    def check_active(func):
        """
        Decorator that raises an error if the Repo context manager is inactive.
        """

        def wrapper(self):
            if not self._active:
                raise RuntimeError(
                    f"{Repo.__name__} object is not active."
                    " Wrap in a 'with' statement to query."
                )
            return func(self)

        return wrapper

    @property
    def url(self) -> str:
        """
        URL of the remote repository.
        """
        return self._url

    @property
    @check_active
    def branches(self) -> Iterator[str]:
        """
        Branch names.
        """
        return get_branches(self._clone.path)

    @property
    @check_active
    def tags(self) -> Iterator[str]:
        """
        Tag names.
        """
        return get_tags(self._clone.path)

    @property
    @check_active
    def commits(self) -> Iterator[Commit]:
        """
        Main branch commit history.
        """
        return collect_commits(self._clone.path)

    @property
    @check_active
    def revisions(self) -> Iterator[Revision]:
        if not self._blobs:
            raise ValueError("Initialize Repo with `blobs`=`True` to load revisions.")
        return collect_revisions(self._clone.path)

    @property
    @check_active
    def diffs(self) -> Iterator[Diff]:
        """
        File-level changes in the repository.
        """
        if not self._blobs:
            raise ValueError("Initialize Repo with `blobs`=`True` to load diffs.")
        return collect_diffs(self._clone.path)
