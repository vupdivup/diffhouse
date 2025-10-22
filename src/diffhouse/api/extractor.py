from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Generic, Iterator, TypeVar

from diffhouse.entities import Branch, Commit, Diff, FileMod, Tag

if TYPE_CHECKING:
    import pandas as pd  # type: ignore
    import polars as pl  # type: ignore
else:
    try:
        import pandas as pd
    except ImportError:
        pd = None

    try:
        import polars as pl
    except ImportError:
        pl = None

T = TypeVar('T', Branch, Tag, Commit, FileMod, Diff)


class Extractor(Generic[T]):
    """Extraction interface for mining a specific type of Git object.

    Acts as an iterable and provides helpers to integrate with data
    analysis libraries.
    """

    def __init__(
        self, path_to_repo: Path, extractor_func: Callable[[Path], Iterator[T]]
    ) -> None:
        """Initialize the extractor.

        Args:
            path_to_repo: Path to the local git repository.
            extractor_func: Function to extract data from the repository.

        """
        self.path_to_repo = path_to_repo
        self.extractor_func = extractor_func

    def __iter__(self) -> Iterator[T]:
        """Extract and iterate over Git objects.

        Data is loaded lazily for memory-efficient processing.

        Yields:
            Extracted Git objects.

        """
        return self._extract()

    def _extract(self) -> Iterator[T]:
        """Extract data using the provided extractor function.

        Yields:
            Extracted Git objects.

        """
        return self.extractor_func(self.path_to_repo)

    def pd(self) -> pd.DataFrame:
        """Extract data into a pandas DataFrame.

        Returns:
            A pandas DataFrame containing the results.

        Raises:
            ImportError: If pandas is not installed.

        """
        if pd is None:
            raise ImportError('pandas is not installed.')
        return pd.DataFrame(self._extract())

    def pl(self) -> pl.DataFrame:
        """Extract data into a polars DataFrame.

        Returns:
            A polars DataFrame containing the results.

        """
        if pl is None:
            raise ImportError('Polars is not installed.')
        return pl.DataFrame(self._extract())
