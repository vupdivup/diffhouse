import polars as pl
import pytest
from rapidfuzz import fuzz

from diffhouse import Repo

from .github import sample_github_endpoint
from .utils import create_failure_msg


def test_branches(repo: Repo):
    """Test that an extract of GitHub branches matches `repo.branches`."""
    branches_gh = [
        b['name']
        for b in sample_github_endpoint(repo.location, 'branches', 200, 50)
    ]

    for branch in branches_gh:
        assert branch in repo.branches, create_failure_msg(
            'Branch missing locally', {'branch': branch}
        )


def test_tags(repo: Repo):
    """Test that an extract of GitHub tags matches `repo.tags`."""
    tags_gh = [
        t['name']
        for t in sample_github_endpoint(repo.location, 'tags', 200, 50)
    ]

    for tag in tags_gh:
        assert tag in repo.tags, create_failure_msg(
            'Tag missing locally', {'tag': tag}
        )


def test_commits(commits_df: pl.DataFrame, commits_gh: pl.DataFrame):
    """Test that an extract of commits from GitHub matches `repo.commits`."""
    suffixed = commits_gh.rename(
        {col: f'{col}_gh' for col in commits_gh.columns}
    )

    joined = commits_df.join(
        suffixed, left_on='commit_hash', right_on='commit_hash_gh', how='full'
    )

    # ensure all GitHub commits are found locally
    assert joined.filter(pl.col('commit_hash').is_null()).is_empty()

    joined = joined.filter(pl.col('commit_hash_gh').is_not_null())

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
        assert errors.is_empty(), errors.to_dicts()

    # compare commit messages (fuzzy match)
    message_mismatches = joined.filter(
        pl.struct('subject', 'body', 'message_gh').map_elements(
            lambda x: fuzz.ratio(x['subject'] + x['body'], x['message_gh']) < 90
        )
    )

    assert message_mismatches.is_empty(), repr(message_mismatches.to_dicts())


def test_shortstats(commits_df, shortstats_gh):
    """Test that a sample of commit shortstats from GitHub matches `repo.commits`."""
    suffixed = shortstats_gh.rename(
        {col: f'{col}_gh' for col in shortstats_gh.columns}
    )

    joined = commits_df.join(
        suffixed, left_on='commit_hash', right_on='commit_hash_gh', how='inner'
    )

    for col in ('lines_added', 'lines_deleted', 'files_changed'):
        errors = joined.filter(pl.col(col) != pl.col(f'{col}_gh'))
        assert errors.is_empty(), repr(errors.to_dicts())


if __name__ == '__main__':
    pytest.main([__file__])
