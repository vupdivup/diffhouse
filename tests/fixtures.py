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
def commits__diffhouse(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of `repo.commits`.

    Datetime strings are converted to objects.
    """
    return pl.DataFrame(repo.commits)


@pytest.fixture(scope='session')
def changed_files__diffhouse(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of `repo.changed_files`."""
    return pl.DataFrame(repo.changed_files)


@pytest.fixture(scope='session')
def diffs__diffhouse(repo: Repo) -> pl.LazyFrame:
    """Fixture that provides a DataFrame of `repo.diffs`."""
    return pl.DataFrame(repo.diffs).lazy()


@pytest.fixture(scope='session')
def commits__github(repo: Repo) -> list[dict]:
    """Fixture that provides commits sampled from GitHub API."""
    return [
        {
            'commit_hash': c['sha'],
            'author_name': c['commit']['author']['name'],
            'author_email': c['commit']['author']['email'],
            'author_date': c['commit']['author']['date'],
            'committer_name': c['commit']['committer']['name'],
            'committer_email': c['commit']['committer']['email'],
            'committer_date': c['commit']['committer']['date'],
            'message': c['commit']['message'],
        }
        for c in sample_github_endpoint(
            repo.source, 'commits', GITHUB_COMMITS_SAMPLE_SIZE
        )
    ]


@pytest.fixture(scope='session')
def changed_files__github(
    repo: Repo, commits__diffhouse: pl.DataFrame
) -> list[dict]:
    """Fixture that provides a list of file changes from the GitHub API.

    Samples non-merge commits only.
    """
    # get k random non-merge commits
    selected_commits = random.sample(
        commits__diffhouse.filter(
            # data quality for commits with too many changed files is often poor
            # this is true for both local & GitHub, so excluding them here
            (pl.col('is_merge').not_()) & (pl.col('files_changed') < 10)
        )['commit_hash'].to_list(),
        k=GITHUB_SHORTSTATS_SAMPLE_SIZE,
    )

    patches = [
        get_github_response(repo.source, f'commits/{c}').json()
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
