import pytest

from diffhouse import Repo
from diffhouse.api.exceptions import FilterError, GitError, NotClonedError
from tests.constants import INVALID_URL, VALID_URL


def test_invalid_url() -> None:
    """Test that initializing `Repo` with an invalid URL raises an exception."""
    with pytest.raises(GitError):
        Repo(INVALID_URL).clone()


def test_no_blobs() -> None:
    """Test that initializing `Repo` with `blobs`=`False` does not load diffs."""
    r = Repo(VALID_URL, blobs=False).clone()
    with pytest.raises(FilterError):
        _ = r.filemods

    with pytest.raises(FilterError):
        _ = r.diffs

    r.dispose()


def test_path_as_source() -> None:
    """Test that initializing `Repo` with a local path works correctly."""
    r = Repo('.', blobs=True)

    assert r.source.startswith('file://')


def test_incorrect_member_access() -> None:
    """Test that accessing members in incorrect states raises exceptions."""
    # no attribute should be available without clone() or context manager
    extractors = []
    attrs = ('branches', 'tags', 'commits', 'filemods', 'diffs')

    r = Repo(VALID_URL)
    for attr in attrs:
        with pytest.raises(NotClonedError):
            getattr(r, attr)

    r.clone()

    extractors = [getattr(r, attr) for attr in attrs]

    r.dispose()

    for extractor in extractors:
        with pytest.raises(NotClonedError):
            _ = list(extractor)

    # after dispose(), no attribute should be available
    for attr in ('branches', 'tags', 'commits', 'filemods', 'diffs'):
        with pytest.raises(NotClonedError):
            getattr(r, attr)
