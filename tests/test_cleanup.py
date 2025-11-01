import subprocess
import tempfile
import time
from pathlib import Path

import psutil
import pytest


def test_cleanup() -> None:
    """Test that temporary files are cleaned up properly after an interrupted run."""
    DUMMY_PATH = 'tests.dummy'
    root = Path('.').resolve()

    p = subprocess.Popen(
        ['uv', 'run', '--no-default-groups', 'python', '-m', DUMMY_PATH],
        cwd=root,
    )

    # abruptly kill the process
    time.sleep(3)

    # p.send_signal(signal.CTRL_BREAK_EVENT)

    # need psutil to recursively kill child processes
    parent = psutil.Process(p.pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()

    assert not is_cleanup_complete()

    subprocess.Popen(
        [
            'uv',
            'run',
            '--no-default-groups',
            'python',
            '-c',
            'import diffhouse',
        ],
        cwd=root,
    ).wait()

    assert is_cleanup_complete()


def is_cleanup_complete() -> bool:
    """Check if any temp directories created by diffhouse still exist."""
    temp_dir = Path(tempfile.gettempdir())
    for item in temp_dir.iterdir():
        if item.is_dir() and item.name.startswith('diffhouse_'):
            return False
    return True


if __name__ == '__main__':
    pytest.main([__file__])
