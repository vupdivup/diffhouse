"""Tests to validate data of extracted entities internally."""

from diffhouse import Repo

from .fixtures import repo  # noqa: F401


def test_validity__commits(repo: Repo) -> None:  # noqa: F811
    """Test that extracted commit data is valid."""
    for c in repo.commits:
        assert len(c.commit_hash) == 40
        assert c.is_merge or len(c.parents) < 2

        for p in c.parents:
            assert len(p) == 40

        # note: not testing names or emails as they can be arbitrary strings

        assert c.lines_added >= 0
        assert c.lines_deleted >= 0
        assert c.files_changed >= 0


def test_validity__changed_files(repo: Repo) -> None:  # noqa: F811
    """Test that extracted changed file data is valid."""
    for f in repo.changed_files:
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
