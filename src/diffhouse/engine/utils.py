import hashlib
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
    return dt[:10] + 'T' + dt[11:19] + dt[20:23] + ':' + dt[-2:]


def split_stream(
    f: StringIO, sep: str, chunk_size: int = 1024
) -> Iterator[str]:
    """Split a stream into parts based on a separator.

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

        if sep in buffer:
            parts = buffer.split(sep)
            for part in parts[:-1]:
                yield part
            buffer = parts[-1]
