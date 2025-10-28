"""Tests to validate data of extracted entities internally."""

from datetime import datetime

from diffhouse import Repo
from tests.fixtures import repo  # noqa: F401


def test_validity__branches(repo: Repo) -> None:  # noqa: F811
    """Test that extracted branch data is valid."""
    for b in repo.branches:
        assert b.name != ''
        assert ' ' not in b.name
        assert ': ' not in b.name


def test_validity__tags(repo: Repo) -> None:  # noqa: F811
    """Test that extracted tag data is valid."""
    for t in repo.tags:
        assert t.name != ''
        assert ' ' not in t.name
        assert ': ' not in t.name


def test_validity__commits(repo: Repo) -> None:  # noqa: F811
    """Test that extracted commit data is valid."""
    for c in repo.commits:
        assert len(c.commit_hash) == 40
        assert c.is_merge or len(c.parents) < 2

        for p in c.parents:
            assert len(p) == 40

        for dt in (
            c.date,
            c.date_local,
            c.author_date,
            c.author_date_local,
        ):
            assert isinstance(dt, datetime)
            assert dt.tzinfo is None  # all datetimes are naive

        # note: not testing names or emails as they can be arbitrary strings

        assert c.lines_added >= 0
        assert c.lines_deleted >= 0
        assert c.files_changed >= 0


def test_validity__filemods(repo: Repo) -> None:  # noqa: F811
    """Test that extracted file modification data is valid."""
    for f in repo.filemods:
        assert len(f.commit_hash) == 40

        assert f.path_a != ''
        assert f.path_b != ''

        assert f.change_type in ['A', 'D', 'M', 'R', 'C', 'T', 'U']

        assert f.path_a == f.path_b or f.change_type in ['R', 'C']
        assert f.similarity == 100 or f.change_type in ['R', 'C']

        assert f.lines_added >= 0
        assert f.lines_deleted >= 0


def test_validity__diffs(repo: Repo) -> None:  # noqa: F811
    """Test that extracted diff data is valid."""
    for d in repo.diffs:
        assert len(d.commit_hash) == 40

        assert d.lines_added >= 0
        assert d.lines_deleted >= 0

        assert len(d.additions) == d.lines_added
        assert len(d.deletions) == d.lines_deleted
