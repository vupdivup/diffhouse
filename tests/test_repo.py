import pytest

from diffhouse import Repo

from .constants import INVALID_URL, VALID_URL


def test_invalid_url():
    """Test that initializing `Repo` with an invalid URL raises an exception."""
    with pytest.raises(Exception):
        Repo(INVALID_URL).load()


def test_no_blobs():
    """Test that initializing `Repo` with `blobs`=`False` does not load diffs."""
    r = Repo(VALID_URL, blobs=False).load()
    with pytest.raises(ValueError):
        r.changed_files

    with pytest.raises(ValueError):
        r.diffs


def test_path_as_location():
    """Test that initializing `Repo` with a local path works correctly."""
    r = Repo('.', blobs=True).load()

    assert r.location.startswith('file://')


def test_streaming():
    """Test that streaming methods output the same results as eager loading."""
    with Repo(VALID_URL, blobs=True) as r:
        commits_streamed = list(r.stream_commits())
        changed_files_streamed = list(r.stream_changed_files())
        diffs_streamed = list(r.stream_diffs())

    repo_eager = r.load()

    assert len(commits_streamed) == len(repo_eager.commits)
    assert len(changed_files_streamed) == len(repo_eager.changed_files)
    assert len(diffs_streamed) == len(repo_eager.diffs)


def test_incorrect_member_access():
    """Test that accessing members in incorrect states raises exceptions."""
    # no attribute should be available without load() or context manager
    r0 = Repo(VALID_URL)
    for attr in ('branches', 'tags', 'commits', 'changed_files', 'diffs'):
        with pytest.raises(RuntimeError):
            getattr(r0, attr)

    for func in ('stream_commits', 'stream_changed_files', 'stream_diffs'):
        with pytest.raises(RuntimeError):
            getattr(r0, func)()

    # only branches and tags attributes should be available within context manager
    with Repo(VALID_URL, blobs=True) as r1:
        for attr in ('commits', 'changed_files', 'diffs'):
            with pytest.raises(RuntimeError):
                getattr(r1, attr)

    # streaming methods should be unavailable when using load()
    r2 = Repo(VALID_URL, blobs=True).load()
    for member in ('stream_commits', 'stream_changed_files', 'stream_diffs'):
        with pytest.raises(RuntimeError):
            getattr(r2, member)()
