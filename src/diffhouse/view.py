from __future__ import annotations  # stringify type hints

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # for static type checking only
    import pandas as pd
    import polars as pl
else:
    try:
        import pandas as pd
    except ImportError:
        pd = None

    try:
        import polars as pl
    except ImportError:
        pl = None


class View:
    def __init__(self, items: Iterator[dict], lazy: bool = False):
        self.lazy = lazy
        self._loaded = False

        if lazy:
            self._iter = items
        else:
            self._items = list(items)

    def __iter__(self) -> Iterator[dict]:
        if self.lazy and self._loaded:
            raise RuntimeError('Stream has already been consumed.')
        self._loaded = True
        return self._iter if self.lazy else iter(self._items)

    def to_polars(self) -> pl.DataFrame:
        if not pl:
            raise ImportError('Polars is not installed.')
        return pl.DataFrame(self)

    def to_pandas(self) -> pd.DataFrame:
        if not pd:
            raise ImportError('Pandas is not installed.')
        return pd.DataFrame(self)
