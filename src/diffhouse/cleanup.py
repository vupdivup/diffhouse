import logging
import os
import shutil
import tempfile
from pathlib import Path

from .constants import PACKAGE_NAME
from .logger import log_to_stdout, package_logger


def remove_residual_resources():
    """Remove residual files created by the package in the system's temporary directory."""
    temp_dir = Path(tempfile.gettempdir())

    for path in temp_dir.iterdir():
        if path.name.startswith(f'{PACKAGE_NAME}_'):
            with log_to_stdout(package_logger, logging.INFO):
                try:
                    package_logger.info(f'Removing residual resource at {path}')
                    if path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(path, onerror=_on_rm_error)
                except Exception:
                    package_logger.warning(
                        f'Failed to remove residual resource at {path}'
                    )


def _on_rm_error(func, path, exc_info):
    """Error handler for `shutil.rmtree`.

    If the error is due to a read-only file (true for some git resources),
    attempt to make it writable.
    """
    import stat

    # try to make it writable and retry
    os.chmod(path, stat.S_IWRITE)
    func(path)
