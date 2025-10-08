import random
from datetime import datetime as dt
from datetime import timezone as tz
from difflib import SequenceMatcher

import polars as pl
import pytest

from diffhouse import Repo

from . import github
from .constants import INVALID_URL, REPOS, VALID_URL
from .utils import create_failure_msg

# randomly select 3 repos for testing to keep it relatively short
SELECTED_REPOS = random.sample(REPOS, 3)


@pytest.fixture(scope='module', params=SELECTED_REPOS)
def repo(request) -> Repo:
    """Fixture that provides a `Repo` instance for a given GitHub URL."""
    return Repo(request.param, blobs=True).load()


@pytest.fixture(scope='module')
def commits_df(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of `repo.commits`."""
    return pl.DataFrame(repo.commits)


@pytest.fixture(scope='module')
def changed_files_df(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of `repo.changed_files`."""
    return pl.DataFrame(repo.changed_files)


@pytest.fixture(scope='module')
def diffs_df(repo: Repo) -> pl.DataFrame:
    """Fixture that provides a DataFrame of `repo.diffs`."""
    return pl.DataFrame(repo.diffs)


def test_branches(repo: Repo):
    """Test that an extract of GitHub branches matches `repo.branches`."""
    branches_gh = [b['name'] for b in github.get_branches(repo.location)]

    for branch in branches_gh:
        assert branch in repo.branches


def test_tags(repo: Repo):
    """Test that an extract of GitHub tags matches `repo.tags`."""
    tags_gh = [t['name'] for t in github.get_tags(repo.location)]

    for tag in tags_gh:
        assert tag in repo.tags


def test_commits_vs_github(repo: Repo, commits_df: pl.DataFrame):
    """Test that an extract of commits from GitHub matches `repo.commits`."""
    commits_gh = github.get_commits(repo.location)

    for commit_gh in commits_gh:
        commit_hash_gh = commit_gh['sha']
        commit_local = commits_df.filter(
            pl.col('commit_hash') == commit_hash_gh
        )

        assert not commit_local.is_empty()

        commit_local = commit_local.row(0, named=True)

        comparisons = (
            (
                commit_local['author_name'],
                commit_gh['commit']['author']['name'],
            ),
            (
                commit_local['author_email'],
                commit_gh['commit']['author']['email'],
            ),
            (
                commit_local['committer_name'],
                commit_gh['commit']['committer']['name'],
            ),
            (
                commit_local['committer_email'],
                commit_gh['commit']['committer']['email'],
            ),
        )

        for local, remote in comparisons:
            assert local == remote, create_failure_msg(
                'Commit metadata differs',
                {
                    'commit': commit_hash_gh,
                    'local': local,
                    'remote': remote,
                },
            )

        message_local = f'{commit_local["subject"]}\n\n{commit_local["body"]}'

        # GitHub commit messages have varied line endings
        message_gh = (
            commit_gh['commit']['message'].strip().replace('\r\n', '\n')
        )

        similarity = SequenceMatcher(
            None, message_local.strip(), message_gh
        ).ratio()

        # commit message similarity
        assert similarity > 0.9, create_failure_msg(
            'Commit messages differ',
            {
                'commit': commit_hash_gh,
                'parsed message': repr(message_local),
                'github message': repr(message_gh),
            },
        )

        # GitHub commit date is in UTC by default
        commit_date_gh = dt.strptime(
            commit_gh['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ'
        ).replace(tzinfo=tz.utc)

        commit_date_local = dt.strptime(
            commit_local['author_date'], '%Y-%m-%dT%H:%M:%S%z'
        ).astimezone(tz.utc)

        assert commit_date_local == commit_date_gh


def test_lines_changed__commits_vs_files(
    commits_df: pl.DataFrame, changed_files_df: pl.DataFrame
):
    """Test that the number of line changes in `repo.commits` matches `repo.changed_files`."""
    commits = commits_df.select('commit_hash', 'lines_added', 'lines_deleted')
    changed_files = changed_files_df.select(
        'commit_hash', 'lines_added', 'lines_deleted'
    )

    files_grouped = changed_files.group_by('commit_hash').agg(
        pl.sum('lines_added'), pl.sum('lines_deleted')
    )

    joined = commits.join(files_grouped, on='commit_hash', how='left').fill_nan(
        0
    )

    errors = joined.filter(
        (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
    )

    assert errors.is_empty(), f'Errors: {errors.to_dicts()}'


def test_files_changed__commits_vs_files(
    commits_df: pl.DataFrame, changed_files_df: pl.DataFrame
):
    """Test that the number of files changed in `repo.commits` matches `repo.changed_files`."""
    commits = commits_df.select('commit_hash', 'files_changed')
    changed_files = changed_files_df.select('commit_hash')

    files_grouped = changed_files.group_by('commit_hash').agg(
        pl.len().alias('files_changed')
    )

    joined = commits.join(files_grouped, on='commit_hash', how='left').fill_nan(
        0
    )

    errors = joined.filter(
        (pl.col('files_changed') != pl.col('files_changed_right'))
    )

    # for commits with many changed files, `changed_files` may be off
    assert len(errors) / len(joined) < 0.01, f'Errors: {errors.to_dicts()}'


def test_lines_changed__files_vs_diffs(
    changed_files_df: pl.DataFrame, diffs_df: pl.DataFrame
):
    """Test that the number of line changes in `repo.changed_files` matches `repo.diffs`."""
    # using lazy loading as this is an expensive operation
    changed_files = changed_files_df.lazy().select(
        'commit_hash', 'changed_file_id', 'lines_added', 'lines_deleted'
    )

    diffs = diffs_df.lazy().select(
        'commit_hash', 'changed_file_id', 'lines_added', 'lines_deleted'
    )

    diffs_grouped = diffs.group_by('commit_hash', 'changed_file_id').agg(
        pl.sum('lines_added'), pl.sum('lines_deleted')
    )

    joined = changed_files.join(
        diffs_grouped, on=['commit_hash', 'changed_file_id'], how='left'
    )

    errors = joined.filter(
        (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
    ).collect()

    joined_count = joined.select(pl.len()).collect().item()

    # allow a bit of wiggle room as line change counts can be different for
    # `git log shortstat` and `git log -p`
    assert len(errors) / joined_count < 0.01, (
        f'Commits: {errors["commit_hash"].to_list()}'
    )


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


def test_location_as_path():
    """Test that initializing `Repo` with a local path works correctly."""
    r = Repo('.', blobs=True).load()

    assert r.location.startswith('file://')


def test_streaming():
    """Test that streaming methods work correctly."""
    with Repo(VALID_URL, blobs=True) as r:
        commits_streamed = list(r.stream_commits())
        changed_files_streamed = list(r.stream_changed_files())
        diffs_streamed = list(r.stream_diffs())

    repo_eager = r.load()

    assert len(commits_streamed) == len(repo_eager.commits)
    assert len(changed_files_streamed) == len(repo_eager.changed_files)
    assert len(diffs_streamed) == len(repo_eager.diffs)

    def test_context_manager_attr_access_raises():
        """Test that accessing attributes raises an error when the repo is used as a context manager."""
        with Repo(VALID_URL, blobs=True) as r:
            for attr in [
                'branches',
                'tags',
                'commits',
                'changed_files',
                'diffs',
            ]:
                with pytest.raises(RuntimeError):
                    getattr(r, attr)


if __name__ == '__main__':
    pytest.main()
