import hashlib

from .constants import UNIT_SEPARATOR


def hash(*args: str) -> str:
    """
    Create a deterministic hash. Not meant for cryptographic security.
    """
    m = hashlib.md5(UNIT_SEPARATOR.join(args).encode())
    return m.hexdigest()
