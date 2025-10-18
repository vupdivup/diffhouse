import logging
from datetime import datetime as dt
from datetime import timezone as tz

import polars as pl
import pytest
from rapidfuzz import fuzz

from diffhouse import Repo

from .fixtures import (  # noqa: F401
    changed_files__github,
    changed_files_df,
    commits__github,
    commits_df,
    repo,
)
from .github import sample_github_endpoint
from .utils import select_keys

logger = logging.getLogger()


def test_branches(repo: Repo) -> None:  # noqa: F811
    """Test that an extract of GitHub branches matches `repo.branches`."""
    branches_gh = [
        b['name']
        for b in sample_github_endpoint(repo.location, 'branches', 200, 50)
    ]

    logger.info(
        f'Comparing {len(branches_gh)} branches between GitHub and local'
    )

    for branch in branches_gh:
        assert branch in repo.branches


def test_tags(repo: Repo) -> None:  # noqa: F811
    """Test that an extract of GitHub tags matches `repo.tags`."""
    tags_gh = [
        t['name']
        for t in sample_github_endpoint(repo.location, 'tags', 200, 50)
    ]

    logger.info(f'Comparing {len(tags_gh)} tags between GitHub and local')

    for tag in tags_gh:
        assert tag in repo.tags


def test_commits(commits_df: pl.DataFrame, commits__github: list[dict]) -> None:  # noqa: F811
    """Test that an extract of commits from GitHub matches `repo.commits`."""
    logger.info(
        f'Comparing {len(commits__github)} commits between GitHub and local'
    )

    for c_gh in commits__github:
        c_local = commits_df.filter(
            pl.col('commit_hash') == c_gh['commit_hash']
        )

        assert len(c_local) == 1, c_gh['commit_hash']

        c_local = c_local.row(0, named=True)

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


def test_changed_files(
    changed_files_df: pl.DataFrame,  # noqa: F811
    changed_files__github: list[dict],  # noqa: F811
) -> None:
    """Test that an extract of changed files from GitHub matches `repo.changed_files`."""
    logger.info(
        f'Comparing {len(changed_files__github)} changed files between GitHub and local'
    )

    for cf_gh in changed_files__github:
        cf_local = changed_files_df.filter(
            (pl.col('commit_hash') == cf_gh['commit_hash'])
            & (pl.col('path_b') == cf_gh.get('path_b'))
        )

        assert len(cf_local) == 1, cf_gh['commit_hash']

        cf_local = cf_local.row(0, named=True)

        if cf_local['lines_added'] == 0 and cf_local['lines_deleted'] == 0:
            # local may omit lines_added/lines_deleted for binary files
            continue

        comparison_fields = [
            'commit_hash',
            'path_a',
            'path_b',
            'lines_added',
            'lines_deleted',
        ]

        assert select_keys(cf_local, comparison_fields) == select_keys(
            cf_gh, comparison_fields
        )


if __name__ == '__main__':
    pytest.main([__file__])
