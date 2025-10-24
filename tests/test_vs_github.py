import logging
from datetime import datetime as dt
from datetime import timezone as tz

import polars as pl
import pytest
from rapidfuzz import fuzz

from diffhouse import Repo
from tests.fixtures import (  # noqa: F401
    commits__diffhouse,
    commits__github,
    filemods__diffhouse,
    filemods__github,
    repo,
)
from tests.github import sample_github_endpoint
from tests.utils import select_keys

logger = logging.getLogger()


def test_branches(repo: Repo) -> None:  # noqa: F811
    """Test that an extract of GitHub branches matches `repo.branches`."""
    branches_gh = [
        b['name']
        for b in sample_github_endpoint(repo.source, 'branches', 200, 50)
    ]

    branches_local = [b.name for b in repo.branches]

    logger.info(
        f'Comparing {len(branches_gh)} branches between GitHub and local'
    )

    for branch in branches_gh:
        assert branch in branches_local


def test_tags(repo: Repo) -> None:  # noqa: F811
    """Test that an extract of GitHub tags matches `repo.tags`."""
    tags_gh = [
        t['name'] for t in sample_github_endpoint(repo.source, 'tags', 200, 50)
    ]

    tags_local = [t.name for t in repo.tags]

    logger.info(f'Comparing {len(tags_gh)} tags between GitHub and local')

    for tag in tags_gh:
        assert tag in tags_local


def test_commits(
    commits__diffhouse: pl.DataFrame,  # noqa: F811
    commits__github: list[dict],  # noqa: F811
) -> None:
    """Test that an extract of commits from GitHub matches `repo.commits`."""
    logger.info(
        f'Comparing {len(commits__github)} commits between GitHub and local'
    )

    for c_gh in commits__github:
        c_local = commits__diffhouse.filter(
            pl.col('commit_hash') == c_gh['commit_hash']
        )

        assert len(c_local) == 1, c_gh['commit_hash']

        c_local = c_local.row(0, named=True)

        assert c_local['in_main']

        comparison_fields = [
            'commit_hash',
            'author_name',
            'author_email',
            'committer_name',
            'committer_email',
        ]

        assert select_keys(c_local, comparison_fields) == select_keys(
            c_gh, comparison_fields
        )

        # convert and compare datetimes in UTC
        for field in ['author_date', 'committer_date']:
            assert dt.fromisoformat(c_local[field]).astimezone(
                tz.utc
            ) == dt.fromisoformat(c_gh[field].replace('Z', '+00:00')), c_gh[
                'commit_hash'
            ]

        # compare commit message with fuzzy matching
        assert (
            fuzz.ratio(
                (
                    c_local['message_subject']
                    + '\n\n'
                    + c_local['message_body']
                ).strip(),
                c_gh['message'],
            )
            >= 90
        ), c_gh['commit_hash']


def test_filemods(
    filemods__diffhouse: pl.DataFrame,  # noqa: F811
    filemods__github: list[dict],  # noqa: F811
) -> None:
    """Test that an extract of GitHub file mods matches `repo.filemods`."""
    logger.info(
        f'Comparing {len(filemods__github)} file mods between GitHub and local'
    )

    for f_gh in filemods__github:
        f_local = filemods__diffhouse.filter(
            (pl.col('commit_hash') == f_gh['commit_hash'])
            & (pl.col('path_b') == f_gh.get('path_b'))
        )

        assert len(f_local) == 1, f_gh['commit_hash']

        f_local = f_local.row(0, named=True)

        if f_local['lines_added'] == 0 and f_local['lines_deleted'] == 0:
            # local may omit lines_added/lines_deleted for binary files
            continue

        comparison_fields = [
            'commit_hash',
            'path_a',
            'path_b',
            'lines_added',
            'lines_deleted',
        ]

        assert select_keys(f_local, comparison_fields) == select_keys(
            f_gh, comparison_fields
        )


if __name__ == '__main__':
    pytest.main([__file__])
