from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Iterator

from diffhouse.entities import GitObject

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


class Extractor:
    """Extraction interface for mining a set of Git objects.

    Supports data streaming and converting results into various formats,
    including native Python representations and data analysis interfaces.
    """

    def __init__(self, iter_fn: Callable[[], Iterator[GitObject]]) -> None:
        """Initialize the extractor.

        Args:
            iter_fn: A callable that returns an iterator over Git objects.

        """
        self._extract = iter_fn

    def __iter__(self) -> Iterator[GitObject]:
        """Extract and iterate over Git objects.

        Items are processed on demand for memory efficiency.

        Yields:
            Extracted Git objects.

        """
        return self._extract()

    def iter_dicts(self) -> Iterator[dict]:
        """Extract and iterate over Git objects as dictionaries.

        Items are processed on demand for memory efficiency.

        Yields:
            Dictionary representations of Git objects.

        """
        for obj in self._extract():
            yield obj.to_dict()

    def to_pandas(self) -> pd.DataFrame:
        """Extract data into a pandas DataFrame.

        Returns:
            A pandas DataFrame containing the results.

        Raises:
            ImportError: If pandas is not installed.

        """
        if pd is None:
            raise ImportError('pandas is not installed.')
        return pd.DataFrame(self._extract())

    def pd(self) -> pd.DataFrame:
        """Shorthand for `to_pandas()`."""
        return self.to_pandas()

    def to_polars(self) -> pl.DataFrame:
        """Extract data into a Polars DataFrame.

        Returns:
            A Polars DataFrame containing the results.

        Raises:
            ImportError: If Polars is not installed.

        """
        if pl is None:
            raise ImportError('Polars is not installed.')
        return pl.DataFrame(self._extract())

    def pl(self) -> pl.DataFrame:
        """Shorthand for `to_polars()`."""
        return self.to_polars()

    def to_list(self) -> list[GitObject]:
        """Extract data into a list.

        Returns:
            A list containing the extracted Git objects.

        """
        return list(self._extract())

    def to_dicts(self) -> list[dict]:
        """Extract data into a list of dictionaries.

        Returns:
            A list of dictionaries representing the extracted Git objects.

        """
        return [obj.to_dict() for obj in self._extract()]
