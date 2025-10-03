from collections.abc import Iterator

from .cloning import TempClone
from .engine import (
    ChangedFile,
    Commit,
    Diff,
    collect_changed_files,
    collect_commits,
    collect_diffs,
    get_branches,
    get_tags,
)


class Repo:
    """Git repository wrapper providing on-demand access to metadata.

    When used in a `with` statement, it creates a clone in the background for
    querying.
    """

    # TODO: verbose
    def __init__(self, location: str, blobs: bool = False):
        """Initialize the repository. `location` can be a remote URL or a local path.

        If `blobs` is `True`, load file content for diffs as well. This requires
        a complete clone and may take a long time.
        """
        # TODO: local path
        self._blobs = blobs
        self._location = location.strip()
        self._active = False
        self._loaded = False

        self._branches = None
        self._tags = None
        self._commits = None
        self._changed_files = None
        self._diffs = None

    def __enter__(self):
        self._clone = TempClone(self.url, shallow=not self._blobs)
        self._clone.__enter__()
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._clone.__exit__(exc_type, exc_value, traceback)
        self._active = False

    def load(self):
        """Load all repository data into memory.

        This is a convenience method to access properties without the `with`
        statement. Not recommended for large repositories.
        """
        self.__enter__()

        # load properties via getters
        self.commits
        self.branches
        self.tags

        if self._blobs:
            self.changed_files
            self.diffs

        self.__exit__(None, None, None)

        return self

    def _raise_if_inactive(self):
        """Raise an error if the Repo context manager is inactive."""
        if not self._active:
            raise RuntimeError(
                f'{Repo.__name__} object is not active.'
                " Wrap in a 'with' statement to query."
            )

    @property
    def url(self) -> str:
        """URL of the remote repository."""
        # TODO: get it from git for local paths
        return self._location

    @property
    def branches(self) -> Iterator[str]:
        """Branch names of the repository."""
        if not self._branches:
            self._raise_if_inactive()
            self._branches = list(get_branches(self._clone.path))
        return self._branches

    @property
    def tags(self) -> Iterator[str]:
        """Tag names of the repository."""
        if not self._tags:
            self._raise_if_inactive()
            self._tags = list(get_tags(self._clone.path))
        return self._tags

    @property
    def commits(self) -> Iterator[Commit]:
        """Main branch commit history."""
        if not self._commits:
            self._raise_if_inactive()

            if self._blobs:
                self._commits = list(
                    collect_commits(self._clone.path, shortstats=True)
                )
            else:
                self._commits = list(
                    collect_commits(self._clone.path, shortstats=False)
                )

        return self._commits

    @property
    def changed_files(self) -> Iterator[ChangedFile]:
        """Files changed per commit."""
        if not self._blobs:
            raise ValueError(
                'Initialize Repo with `blobs`=`True` to load changed files.'
            )
        if not self._changed_files:
            self._raise_if_inactive()
            self._changed_files = list(collect_changed_files(self._clone.path))

        return self._changed_files

    @property
    def diffs(self) -> Iterator[Diff]:
        """Line-level changes within a commit."""
        if not self._blobs:
            raise ValueError(
                'Initialize Repo with `blobs`=`True` to load diffs.'
            )
        if not self._diffs:
            self._raise_if_inactive()
            self._diffs = list(collect_diffs(self._clone.path))
        return self._diffs
