from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

import validators

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
    """Git repository wrapper providing access to metadata.

    When used via its `load()` method or in a `with` statement, it sets up and
    queries a temporary clone in the background to retrieve information.

    Examples:
        ```python
        with Repo('https://github.com/user/repo') as r:
            for c in r.commits:
                print(c.commit_hash[:10])
                print(c.author_email)
                print(c.subject)
        ```

    """

    # TODO: verbose
    def __init__(self, location: str, blobs: bool = False):
        """Initialize the repository.

        Args:
            location: URL or local path pointing to a git repository.
            blobs: Whether to load file content and extract associated metadata.

        """
        # Convert location to file URI if not a URL
        self._location = (
            location.strip()
            if validators.url(location)
            else Path(location).resolve().as_uri()
        )

        self._blobs = blobs
        self._active = False
        self._loaded = False

        self._cache = defaultdict(lambda: None)

    def __enter__(self):
        self._clone = TempClone(self._location, shallow=not self._blobs)
        self._clone.__enter__()
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._clone.__exit__(exc_type, exc_value, traceback)
        self._active = False

    def load(self) -> 'Repo':
        """Load all repository data into memory.

        This is a convenience method to access properties without the `with`
        statement. Not recommended for large repositories.

        Returns:
            self

        """
        self.__enter__()

        # load and cache properties via getters
        self._cache['commits'] = list(self.commits)
        self._cache['branches'] = list(self.branches)
        self._cache['tags'] = list(self.tags)

        if self._blobs:
            self._cache['changed_files'] = list(self.changed_files)
            self._cache['diffs'] = list(self.diffs)

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
    def location(self) -> str:
        """Location where the repository was cloned from.

        Can either be a remote URL or a local file URI based on the
        original input.
        """
        return self._location

    @property
    def branches(self) -> Iterable[str]:
        """Branch names of the repository."""
        if self._cache['branches']:
            return self._cache['branches']

        self._raise_if_inactive()
        return get_branches(self._clone.path)

    @property
    def tags(self) -> Iterable[str]:
        """Tag names of the repository."""
        if self._cache['tags']:
            return self._cache['tags']

        self._raise_if_inactive()
        return get_tags(self._clone.path)

    @property
    def commits(self) -> Iterable[Commit]:
        """Main branch commit history."""
        if self._cache['commits']:
            return self._cache['commits']

        self._raise_if_inactive()
        return collect_commits(self._clone.path, shortstats=self._blobs)

    @property
    def changed_files(self) -> Iterable[ChangedFile]:
        """Files changed for each commit."""
        if not self._blobs:
            raise ValueError(
                'Initialize Repo with `blobs`=`True` to load changed files.'
            )

        if self._cache['changed_files']:
            return self._cache['changed_files']

        self._raise_if_inactive()
        return collect_changed_files(self._clone.path)

    @property
    def diffs(self) -> Iterable[Diff]:
        """Line-level changes within commits."""
        if not self._blobs:
            raise ValueError(
                'Initialize Repo with `blobs`=`True` to load diffs.'
            )

        if self._cache['diffs']:
            return self._cache['diffs']

        self._raise_if_inactive()
        return collect_diffs(self._clone.path)
