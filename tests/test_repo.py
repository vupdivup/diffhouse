import random
from datetime import datetime as dt
from datetime import timezone as tz

import polars as pl
import pytest

from diffhouse import Repo

from . import github
from .constants import INVALID_URL, REPOS, VALID_URL

# randomly select 4 repos for testing to keep it relatively short
SELECTED_REPOS = random.sample(REPOS, 4)


@pytest.fixture(scope='module', params=SELECTED_REPOS)
def repo(request) -> Repo:
    """Fixture that provides a `Repo` instance for a given GitHub URL."""
    return Repo(request.param, blobs=True).load()


def test_branches(repo: Repo):
    """Test that an extract of GitHub branches matches `repo.branches`."""
    branches_gh = [b['name'] for b in github.get_branches(repo.url)]

    for branch in branches_gh:
        assert branch in repo.branches


def test_tags(repo: Repo):
    """Test that an extract of GitHub tags matches `repo.tags`."""
    tags_gh = [t['name'] for t in github.get_tags(repo.url)]

    for tag in tags_gh:
        assert tag in repo.tags


def test_commits_vs_github(repo: Repo):
    """Test that an extract of commits from GitHub matches `repo.commits`."""
    commits_gh = github.get_commits(repo.url)

    commits_df = pl.DataFrame(repo.commits)

    for commit_gh in commits_gh:
        commit_hash_gh = commit_gh['sha']
        commit_local = commits_df.filter(
            pl.col('commit_hash') == commit_hash_gh
        )

        assert not commit_local.is_empty()

        commit_local = commit_local.row(0, named=True)

        assert (
            commit_local['author_name'] == commit_gh['commit']['author']['name']
        )
        assert (
            commit_local['author_email']
            == commit_gh['commit']['author']['email']
        )
        assert (
            commit_local['committer_name']
            == commit_gh['commit']['committer']['name']
        )
        assert (
            commit_local['committer_email']
            == commit_gh['commit']['committer']['email']
        )

        # GitHub API line endings are not normalized it seems
        gh_message_clean = commit_gh['commit']['message'].replace('\r\n', '\n')

        assert commit_local['subject'] in gh_message_clean
        assert commit_local['body'] in gh_message_clean

        # GitHub commit date is in UTC by default
        commit_date_gh = dt.fromisoformat(commit_gh['commit']['author']['date'])

        commit_date_local = dt.fromisoformat(
            commit_local['author_date']
        ).astimezone(tz.utc)

        assert commit_date_local == commit_date_gh


def test_lines_changed__commits_vs_files(repo: Repo):
    """Test that the number of line changes in `repo.commits` matches `repo.changed_files`."""
    commits = pl.DataFrame(repo.commits)
    changed_files = pl.DataFrame(repo.changed_files)

    files_grouped = changed_files.group_by('commit_hash').agg(
        pl.sum('lines_added'), pl.sum('lines_deleted')
    )

    joined = commits.join(files_grouped, on='commit_hash', how='left').fill_nan(
        0
    )

    assert joined.filter(
        (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
    ).is_empty()


def test_files_changed__commits_vs_files(repo):
    """Test that the number of files changed in `repo.commits` matches `repo.changed_files`."""
    commits = pl.DataFrame(repo.commits).select('commit_hash', 'files_changed')
    changed_files = pl.DataFrame(repo.changed_files).select('commit_hash')

    files_grouped = changed_files.group_by('commit_hash').agg(
        pl.len().alias('files_changed')
    )

    joined = commits.join(files_grouped, on='commit_hash', how='left').fill_nan(
        0
    )

    errors = joined.filter(
        (pl.col('files_changed') != pl.col('files_changed_right'))
    )

    assert errors.is_empty()


def test_lines_changed__files_vs_diffs(repo: Repo):
    """Test that the number of line changes in `repo.changed_files` matches `repo.diffs`."""
    changed_files = pl.DataFrame(repo.changed_files).select(
        'changed_file_id', 'lines_added', 'lines_deleted'
    )

    diffs = pl.DataFrame(repo.diffs).select(
        'changed_file_id', 'lines_added', 'lines_deleted'
    )

    diffs_grouped = diffs.group_by('changed_file_id').agg(
        pl.sum('lines_added'), pl.sum('lines_deleted')
    )

    joined = changed_files.join(diffs_grouped, on='changed_file_id', how='left')

    errors = joined.filter(
        (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
    )

    # allow a bit of wiggle room as line change counts can be different for
    # `git log shortstat` and `git log -p`
    assert len(errors) / len(joined) < 0.01


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


if __name__ == '__main__':
    pytest.main()
