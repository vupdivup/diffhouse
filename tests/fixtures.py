import random

import polars as pl
import pytest

from diffhouse import Repo

from .constants import (
    GITHUB_COMMITS_SAMPLE_SIZE,
    GITHUB_SHORTSTATS_SAMPLE_SIZE,
    REPOS,
)
from .github import get_github_response, sample_github_endpoint

# randomly select 3 repos for testing to keep it relatively short
SELECTED_REPOS = random.sample(REPOS, 3)


@pytest.fixture(scope='session', params=SELECTED_REPOS)
def repo(request: pytest.FixtureRequest) -> Repo:
    """Fixture that provides a `Repo` instance for a given GitHub URL."""
    return Repo(request.param, blobs=True).load()


@pytest.fixture(scope='session')
def commits_df(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of `repo.commits`.

    Datetime strings are converted to objects.
    """
    df = pl.DataFrame(repo.commits)

    df = df.with_columns(pl.col('author_date').str.to_datetime(time_zone='utc'))
    df = df.with_columns(
        pl.col('committer_date').str.to_datetime(time_zone='utc')
    )
    return df


@pytest.fixture(scope='session')
def changed_files_df(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of `repo.changed_files`."""
    return pl.DataFrame(repo.changed_files)


@pytest.fixture(scope='session')
def diffs_df(repo: Repo) -> pl.LazyFrame:
    """Fixture that provides a DataFrame of `repo.diffs`."""
    return pl.DataFrame(repo.diffs).lazy()


@pytest.fixture(scope='session')
def commits_gh(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of commits sampled from GitHub API."""
    df = pl.DataFrame(
        sample_github_endpoint(
            repo.location, 'commits', GITHUB_COMMITS_SAMPLE_SIZE
        )
    ).lazy()

    # select columns of interest
    df = df.select('sha', 'commit').unnest('commit')
    df = df.select('sha', 'author', 'committer', 'message').rename(
        {'sha': 'commit_hash'}
    )

    # unnest author and committer
    df = df.unnest('author').rename(
        {'name': 'author_name', 'email': 'author_email', 'date': 'author_date'}
    )
    df = df.unnest('committer').rename(
        {
            'name': 'committer_name',
            'email': 'committer_email',
            'date': 'committer_date',
        }
    )

    # convert datetime strings to objects
    df = df.with_columns(pl.col('author_date').str.to_datetime(time_zone='utc'))
    df = df.with_columns(
        pl.col('committer_date').str.to_datetime(time_zone='utc')
    )

    return df.collect()


@pytest.fixture(scope='session')
def changed_files__github(repo: Repo, commits_df: pl.DataFrame) -> list[dict]:
    """Fixture that provides a list of file changes from the GitHub API.

    Samples non-merge commits only.
    """
    # get k random non-merge commits
    selected_commits = random.sample(
        commits_df.filter((pl.col('is_merge').not_()))['commit_hash'].to_list(),
        k=GITHUB_SHORTSTATS_SAMPLE_SIZE,
    )

    patches = [
        get_github_response(repo.location, f'commits/{c}').json()
        for c in selected_commits
    ]

    return [
        {
            'commit_hash': p['sha'],
            'path_b': f['filename'],
            'change_type': f['status'],
            'lines_added': f['additions'],
            'lines_deleted': f['deletions'],
            'path_a': f.get('previous_filename', f['filename']),
        }
        for p in patches
        for f in p['files']
    ]
