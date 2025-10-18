import logging

import polars as pl
import pytest
from rapidfuzz import fuzz

from diffhouse import Repo

from .fixtures import (  # noqa: F401
    changed_files__github,
    changed_files_df,
    commits_df,
    commits_gh,
    repo,
    shortstats_gh,
)
from .github import sample_github_endpoint

logger = logging.getLogger()


def test_branches(repo: Repo) -> None:  # noqa: F811
    """Test that an extract of GitHub branches matches `repo.branches`."""
    branches_gh = [
        b['name']
        for b in sample_github_endpoint(repo.location, 'branches', 200, 50)
    ]

    for branch in branches_gh:
        assert branch in repo.branches, f'Branch {branch} missing locally'


def test_tags(repo: Repo) -> None:  # noqa: F811
    """Test that an extract of GitHub tags matches `repo.tags`."""
    tags_gh = [
        t['name']
        for t in sample_github_endpoint(repo.location, 'tags', 200, 50)
    ]

    for tag in tags_gh:
        assert tag in repo.tags, f'Tag {tag} missing locally'


def test_commits(commits_df: pl.DataFrame, commits_gh: pl.DataFrame) -> None:  # noqa: F811
    """Test that an extract of commits from GitHub matches `repo.commits`."""
    suffixed = commits_gh.rename(
        {col: f'{col}_gh' for col in commits_gh.columns}
    )

    joined = suffixed.join(
        commits_df,
        left_on='commit_hash_gh',
        right_on='commit_hash',
        how='left',
        coalesce=False,
    )

    # ensure we have a match for every commit sampled from GitHub
    assert joined['commit_hash'].is_not_null().all(), (
        'Not all GitHub commits found locally: '
        + repr(joined.filter(pl.col('commit_hash').is_null()).to_dicts())
    )

    logger.info(f'Comparing {len(joined)} commits between GitHub and local')

    # compare fields
    for col in (
        'author_name',
        'author_email',
        'author_date',
        'committer_name',
        'committer_email',
        'committer_date',
    ):
        errors = joined.filter(pl.col(col) != pl.col(f'{col}_gh'))
        assert errors.is_empty(), (
            f'{col} mismatch between GitHub and local: '
            + repr(errors.to_dicts())
        )

    # compare commit messages (fuzzy match)
    message_mismatches = joined.filter(
        pl.struct('message_subject', 'message_body', 'message_gh').map_elements(
            lambda x: fuzz.ratio(
                (x['message_subject'] + '\n\n' + x['message_body']).strip(),
                x['message_gh'],
            )
            < 90
        )
    )

    assert message_mismatches.is_empty(), 'Commit message mismatch: ' + repr(
        message_mismatches.to_dicts()
    )


def test_vs_github__changed_files(
    changed_files_df: pl.DataFrame,  # noqa: F811
    changed_files__github: list[dict],  # noqa: F811
) -> None:
    """Test that an extract of changed files from GitHub matches `repo.changed_files`."""
    for cf_gh in changed_files__github:
        cf_local = changed_files_df.filter(
            (pl.col('commit_hash') == cf_gh['commit_hash'])
            & (pl.col('path_b') == cf_gh.get('path_b'))
        )

        assert len(cf_local) == 1

        cf_local = cf_local.row(0, named=True)

        if cf_local['lines_added'] == 0 and cf_local['lines_deleted'] == 0:
            # local may omit lines_added/lines_deleted for binary files
            continue

        assert cf_local['lines_added'] == cf_gh['lines_added']
        assert cf_local['lines_deleted'] == cf_gh['lines_deleted']
        assert cf_local['path_a'] == cf_gh['path_a']


if __name__ == '__main__':
    pytest.main([__file__])
