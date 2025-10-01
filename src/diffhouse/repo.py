from collections.abc import Iterator
from functools import wraps

from .cloning import TempClone
from .engine import (
    Commit,
    ChangedFile,
    Diff,
    collect_commits,
    collect_changed_files,
    collect_diffs,
    get_branches,
    get_tags,
)


class Repo:
    """
    Git repository wrapper providing on-demand access to metadata.

    When used in a `with` statement, it creates a clone in the background for querying.
    """

    # TODO: verbose
    def __init__(self, location: str, blobs: bool = False):
        """
        Initialize the repository. `location` can be a remote URL or a local path.

        If `blobs` is `True`, load file content for diffs as well. This requires a
        complete clone and may take a long time.
        """
        # TODO: local path
        self._blobs = blobs
        self._location = location.strip()
        self._active = False

    def __enter__(self):
        self._clone = TempClone(self.url, shallow=not self._blobs)
        self._clone.__enter__()
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._clone.__exit__(exc_type, exc_value, traceback)
        self._active = False

    def _check_active(func):
        """
        Decorator that raises an error if the Repo context manager is inactive.
        """

        @wraps(func)
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
        # TODO: get it from git for local paths
        return self._location

    @property
    @_check_active
    def branches(self) -> Iterator[str]:
        """
        Branch names of the repository.
        """
        return get_branches(self._clone.path)

    @property
    @_check_active
    def tags(self) -> Iterator[str]:
        """
        Tag names of the repository.
        """
        return get_tags(self._clone.path)

    @property
    @_check_active
    def commits(self) -> Iterator[Commit]:
        """
        Main branch commit history.
        """
        return collect_commits(self._clone.path)

    # TODO: find a better name

    @property
    @_check_active
    def changed_files(self) -> Iterator[ChangedFile]:
        """
        Files changed per commit.
        """
        if not self._blobs:
            raise ValueError(
                "Initialize Repo with `blobs`=`True` to load changed files."
            )
        return collect_changed_files(self._clone.path)

    @property
    @_check_active
    def diffs(self) -> Iterator[Diff]:
        """
        Code changes per revision.
        """
        if not self._blobs:
            raise ValueError("Initialize Repo with `blobs`=`True` to load diffs.")
        return collect_diffs(self._clone.path)
