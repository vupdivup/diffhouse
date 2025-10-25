from pathlib import Path
from typing import Iterator

import validators

from diffhouse.api import Extractor
from diffhouse.api.exceptions import FilterError, NotClonedError, ParserError
from diffhouse.entities import Branch, Commit, Diff, FileMod, Tag
from diffhouse.git import TempClone
from diffhouse.pipelines import (
    extract_branches,
    extract_commits,
    extract_diffs,
    extract_filemods,
    extract_tags,
)


class Repo:
    """Wrapper around a Git repository.

    `Repo` is the main entry point for mining repositories with diffhouse.
    """

    def __init__(self, source: str, blobs: bool = True):
        """Initialize the repository.

        When sourcing from a local path, the `blobs = False` filter
            may not be available.

        Args:
            source: URL or local path pointing to a Git repository.
            blobs: Whether to load file content. If this is `False`, only

        """
        # Convert source to file URI if not a URL
        self._source = (
            source.strip()
            if validators.url(source)
            else Path(source).resolve().as_uri()
        )

        self._blobs = blobs
        self._active = False

        self._tags = None

    def __enter__(self) -> 'Repo':
        """Set up a temporary clone of the repository.

        Returns:
            self

        """
        return self.clone()

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        """Clean up the temporary clone."""
        self.dispose()

    def __del__(self) -> None:
        """Clean up the temporary clone on deletion."""
        self.dispose()

    def _require_active(self) -> None:
        """Raise an error if the Repo context manager is not active."""
        if not self._active:
            raise NotClonedError()

    def _require_blobs(self) -> None:
        """Raise an error if the Repo was not initialized with `blobs = True`."""
        if not self._blobs:
            raise FilterError('blobs')

    @property
    def branches(self) -> Extractor[Branch]:
        """Branches of the repository."""
        self._require_active()
        return Extractor(
            self._clone.path, lambda p: self._safe_iter(extract_branches(p))
        )

    @property
    def tags(self) -> Extractor[Tag]:
        """Tag names of the repository."""
        self._require_active()
        return Extractor(
            self._clone.path, lambda p: self._safe_iter(extract_tags(p))
        )

    @property
    def commits(self) -> Extractor[Commit]:
        """Commit history of the repository."""
        self._require_active()
        return Extractor(
            self._clone.path,
            lambda p: self._safe_iter(
                extract_commits(p, shortstats=self._blobs)
            ),
        )

    @property
    def filemods(self) -> Extractor[FileMod]:
        """File change metadata for all commits."""
        self._require_blobs()
        self._require_active()
        return Extractor(
            self._clone.path, lambda p: self._safe_iter(extract_filemods(p))
        )

    @property
    def diffs(self) -> Extractor[Diff]:
        """Source code changes for all commits."""
        self._require_blobs()
        self._require_active()
        return Extractor(
            self._clone.path, lambda p: self._safe_iter(extract_diffs(p))
        )

    @property
    def source(self) -> str:
        """Location where the repository was cloned from.

        Can either be a remote URL or a local file URI based on the
        original input.
        """
        return self._source

    def clone(self) -> 'Repo':
        """Set up a temporary clone of the repository.

        This method is an alternative to `with` statements. Call `clean()` to
        free up resources when done.

        Returns:
            self

        """
        self._clone = TempClone(self._source, shallow=not self._blobs)
        self._clone.__enter__()

        self._active = True
        return self

    def dispose(self) -> None:
        """Free up resources associated with the object.

        Only needed when `clone()` is used directly.
        """
        if self._active:
            self._clone.__exit__(None, None, None)
            self._active = False

    def _safe_iter(self, iter_: Iterator) -> Iterator:
        """Wrap a generator for higher-level error handling.

        Args:
            iter_: The generator to wrap.

        Yields:
            Items from the generator.

        """
        try:
            yield from iter_
        except FileNotFoundError as e:
            raise NotClonedError() from e
        except Exception as e:
            raise ParserError('Failed to parse repository data.') from e
