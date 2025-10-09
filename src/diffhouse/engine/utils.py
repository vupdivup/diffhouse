import hashlib
import warnings
from collections.abc import Iterator
from io import StringIO

from .constants import UNIT_SEPARATOR


def hash(*args: str) -> str:
    """Create a deterministic hash. Not meant for cryptographic security."""
    m = hashlib.md5(UNIT_SEPARATOR.join(args).encode())
    return m.hexdigest()


def tweak_git_iso_datetime(dt: str) -> str:
    """Convert git ISO datetime to precise ISO 8601 format.

    Args:
        dt: Git ISO datetime string (*YYYY-MM-DD HH:MM:SS ±HHMM*).

    Returns:
        ISO 8601 formatted datetime string (*YYYY-MM-DDTHH:MM:SS±HH:MM*).

    """
    return dt[:10] + 'T' + dt[11:19] + dt[20:23] + ':' + dt[23:25]


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


def safe_iter(iter: Iterator, warning: str) -> Iterator:
    """Wrap a generator to raise a warning instead of an error if an item fails.

    Failed items are skipped.

    Args:
        iter: The generator to wrap.
        warning: Warning message to display if an item fails.

    Yields:
        Items from the generator.

    """
    while True:
        try:
            next_ = next(iter)
        except StopIteration:
            return
        except Exception:
            warnings.warn(warning)
            continue

        yield next_
