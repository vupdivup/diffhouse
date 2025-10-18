import warnings
from collections.abc import Iterator
from io import StringIO

import xxhash

from .constants import UNIT_SEPARATOR


def fast_hash_64(*args: str) -> str:
    """Fast deterministic hash.

    Args:
        *args: Strings to hash.

    Returns:
        A 64-bit hexadecimal hash string.

    """
    return xxhash.xxh64_hexdigest(UNIT_SEPARATOR.join(args))


def split_stream(
    f: StringIO, sep: str, chunk_size: int = 1024
) -> Iterator[str]:
    """Lazily split a stream into parts based on a separator.

    Args:
        f: Input stream to read from.
        sep: Separator string to split the stream.
        chunk_size: Number of characters to read at a time.

    Yields:
        Parts of the stream split by the separator.

    """
    buffer = ''

    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            # EOF
            if buffer:
                yield buffer
            break

        buffer += chunk

        parts = buffer.split(sep)

        if len(parts) == 1:
            continue

        for part in parts[:-1]:
            yield part

        buffer = parts[-1]


def safe_iter(iter_: Iterator, warning: str) -> Iterator:
    """Wrap a generator to raise a warning instead of an error if an item fails.

    Failed items are skipped.

    Args:
        iter_: The generator to wrap.
        warning: Warning message to display if an item fails.

    Yields:
        Items from the generator.

    """
    while True:
        try:
            next_ = next(iter_)
        except StopIteration:
            return
        except Exception:
            warnings.warn(warning)
            continue

        yield next_
