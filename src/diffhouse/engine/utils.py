import hashlib

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
