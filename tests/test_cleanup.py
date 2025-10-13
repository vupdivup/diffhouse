import subprocess
import tempfile
import time
from pathlib import Path

import pytest


def test_cleanup():
    """Test that temporary files are cleaned up properly after an interrupted run."""
    DUMMY_PATH = 'tests.dummy'
    root = Path('.').resolve()

    p = subprocess.Popen(['uv', 'run', 'python', '-m', DUMMY_PATH], cwd=root)

    # abruptly kill the process
    time.sleep(1)
    p.kill()

    assert not is_cleanup_complete()

    p = subprocess.Popen(
        ['uv', 'run', 'python', '-m', DUMMY_PATH], cwd=root
    ).wait()

    assert is_cleanup_complete()


def is_cleanup_complete():
    """Check if any temp directories created by diffhouse still exist."""
    temp_dir = Path(tempfile.gettempdir())
    for item in temp_dir.iterdir():
        if item.is_dir() and item.name.startswith('diffhouse_'):
            return False
    return True


if __name__ == '__main__':
    pytest.main([__file__])
