from collections.abc import Iterator
from datetime import datetime, timedelta
from io import StringIO

import xxhash

from diffhouse.pipelines.constants import UNIT_SEPARATOR


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

        parts = chunk.split(sep)
        parts[0] = buffer + parts[0]

        if len(parts) == 1:
            continue

        for part in parts[:-1]:
            yield part

        buffer = parts[-1]


def parse_git_timestamp(dtstr: str) -> tuple[datetime, datetime]:
    """Convert a git ISO datetime string to naive datetimes.

    Args:
        dtstr: Git ISO datetime string (*YYYY-MM-DD HH:MM:SS ±HHMM*).

    Returns:
        The datetime in UTC and local time, both naive.

    """
    # indexed slicing is faster than strptime
    yr = int(dtstr[0:4])
    mo = int(dtstr[5:7])
    da = int(dtstr[8:10])
    hr = int(dtstr[11:13])
    mi = int(dtstr[14:16])
    se = int(dtstr[17:19])

    offset_sign = 1 if dtstr[20] == '+' else -1
    offset_hours = int(dtstr[21:23])
    offset_minutes = int(dtstr[23:25])
    offset = timedelta(
        hours=offset_sign * offset_hours, minutes=offset_sign * offset_minutes
    )

    return (
        datetime(yr, mo, da, hr, mi, se) - offset,  # UTC
        datetime(yr, mo, da, hr, mi, se),  # local time
    )
