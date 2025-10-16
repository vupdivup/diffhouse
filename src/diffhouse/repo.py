import logging
from collections.abc import Iterator
from pathlib import Path

import validators

from .core import (
    get_branches,
    get_tags,
    stream_changed_files,
    stream_commits,
    stream_diffs,
)
from .entities import ChangedFile, Commit, Diff
from .git import TempClone
from .utils.logger import log_to_stdout, package_logger


class Repo:
    """Git repository wrapper for querying mined data.

    When used via its `load()` method or in a `with` statement, it sets up a
    temporary clone to retrieve information; this may take long
    depending on the repository size and network speed.
    """

    def __init__(
        self, location: str, blobs: bool = False, verbose: bool = False
    ):
        """Initialize the repository.

        When sourcing from a local path, the `blobs = False` filter
            may not be available.

        Args:
            location: URL or local path pointing to a git repository.
            blobs: Whether to load file content and extract associated metadata.
            verbose: Whether to log progress to stdout.

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
        self._verbose = verbose

        # these two can be accessed in both normal and lazy modes
        # init with None ensures that data is queried when they are accessed
        self._branches = None
        self._tags = None

    def __enter__(self) -> 'Repo':
        """Set up a temporary clone of the repository.

        Returns:
            self

        """
        with log_to_stdout(package_logger, logging.INFO, enabled=self._verbose):
            package_logger.info(f'Cloning {self._location}')

            self._clone = TempClone(self._location, shallow=not self._blobs)
            self._clone.__enter__()

            package_logger.info(f'Cloned into {self._clone.path}')

        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        """Clean up the temporary clone."""
        self._clone.__exit__(exc_type, exc_value, traceback)
        self._active = False

    def load(self) -> 'Repo':
        """Load all repository data into memory.

        This is a convenience method to access objects without the `with`
        statement. For large repositories, take a look at the streaming options
            instead.

        Returns:
            self

        """
        with (
            self,
            log_to_stdout(package_logger, logging.INFO, enabled=self._verbose),
        ):
            # load and cache properties via getters
            package_logger.info('Extracting branches')
            _ = self.branches

            package_logger.info('Extracting tags')
            _ = self.tags

            package_logger.info('Extracting commits')
            self._commits = list(self.stream_commits())

            if self._blobs:
                package_logger.info('Extracting changed files')
                self._changed_files = list(self.stream_changed_files())

                package_logger.info('Extracting diffs')
                self._diffs = list(self.stream_diffs())

            package_logger.info('Load complete')

        self._loaded = True

        return self

    def _require_active(self) -> None:
        """Raise an error if the Repo context manager is not active."""
        if not self._active:
            raise RuntimeError(
                f'{Repo.__name__} object is not active.'
                " Wrap in a 'with' statement to query."
            )

    def _require_loaded(self) -> None:
        """Raise an error if the Repo has not been loaded into memory."""
        if not self._loaded:
            raise RuntimeError(
                f'{Repo.__name__} object is not loaded.'
                " Call the 'load()' method first to load all data into memory."
            )

    def _require_blobs(self) -> None:
        """Raise an error if the Repo was not initialized with `blobs = True`."""
        if not self._blobs:
            raise ValueError(
                'Load `Repo` with `blobs = True` to access this property.'
            )

    @property
    def branches(self) -> list[str]:
        """Branch names of the repository."""
        if not self._branches:
            self._require_active()
            self._branches = get_branches(self._clone.path)
        return self._branches

    @property
    def tags(self) -> list[str]:
        """Tag names of the repository."""
        if not self._tags:
            self._require_active()
            self._tags = get_tags(self._clone.path)
        return self._tags

    @property
    def commits(self) -> list[Commit]:
        """Commit history of the default branch.

        Requires `load()`.
        """
        self._require_loaded()
        return self._commits

    @property
    def changed_files(self) -> list[ChangedFile]:
        """Files of all default-branch commits.

        Requires `load()` and `blobs = True`.
        """
        self._require_loaded()
        self._require_blobs()
        return self._changed_files

    @property
    def diffs(self) -> list[Diff]:
        """Diffs of all default-branch commits.

        Requires `load()` and `blobs = True`.
        """
        self._require_loaded()
        self._require_blobs()
        return self._diffs

    def stream_commits(self) -> Iterator[Commit]:
        """Stream the commit history of the default branch.

        Requires wrapping the `Repo` in a `with` statement.

        Yields:
            Commit data.

        """
        self._require_active()
        return self._safe_stream(
            stream_commits(self._clone.path, shortstats=self._blobs)
        )

    def stream_changed_files(self) -> Iterator[ChangedFile]:
        """Stream the files of all default-branch commits.

        Requires `blobs = True` and wrapping the `Repo` in a `with` statement.

        Yields:
            File change metadata.

        """
        self._require_active()
        self._require_blobs()
        return self._safe_stream(stream_changed_files(self._clone.path))

    def stream_diffs(self) -> Iterator[Diff]:
        """Stream diffs of all default-branch commits.

        Requires `blobs = True` and wrapping the `Repo` in a `with` statement.

        Yields:
            Text diffs.

        """
        self._require_active()
        self._require_blobs()
        return self._safe_stream(stream_diffs(self._clone.path))

    @property
    def location(self) -> str:
        """Location where the repository was cloned from.

        Can either be a remote URL or a local file URI based on the
        original input.
        """
        return self._location

    def _safe_stream(self, iter_: Iterator) -> Iterator:
        """Wrap a generator to raise an error if not consumed in the `with` block.

        Args:
            iter_: The generator to wrap.

        Yields:
            Items from the generator.

        """
        while True:
            try:
                next_ = next(iter_)
            except StopIteration:
                return
            except FileNotFoundError:
                raise RuntimeError(
                    'Generator has to be consumed in the `with` block.'
                ) from None

            yield next_
