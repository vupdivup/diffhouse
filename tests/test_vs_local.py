import polars as pl
import pytest

from .fixtures import changed_files_df, commits_df, diffs_df, repo  # noqa: F401


def test_commits_vs_changed_files(
    commits_df: pl.DataFrame,  # noqa: F811
    changed_files_df: pl.DataFrame,  # noqa: F811
):
    """Test that overlapping data of `repo.commits` and `repo.changed_files` matches."""
    files_grouped = changed_files_df.group_by('commit_hash').agg(
        pl.len().alias('files_changed'),
        pl.col('lines_added').sum().alias('lines_added'),
        pl.col('lines_deleted').sum().alias('lines_deleted'),
    )

    joined = commits_df.join(
        files_grouped, on='commit_hash', how='left', coalesce=False
    ).fill_nan(0)

    errors = joined.filter(
        (pl.col('commit_hash_right').is_null() & (pl.col('files_changed') > 0))
        | (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
        | (pl.col('files_changed') != pl.col('files_changed_right'))
    )

    # for huge commits, shortstat's 'files changed' may differ from actual count
    # of changed files, so allow a bit of wiggle room
    assert len(errors) / len(joined) < 0.01, (
        'Commits and changed files do not match: ' + repr(errors.to_dicts())
    )


def test_changed_files_vs_diffs(
    changed_files_df: pl.DataFrame,  # noqa: F811
    diffs_df: pl.DataFrame,  # noqa: F811
):
    """Test that overlapping data of `repo.changed_files` and `repo.diffs` matches."""
    # using lazy loading as this is an expensive operation
    diffs_grouped = diffs_df.group_by('commit_hash', 'changed_file_id').agg(
        pl.sum('lines_added'), pl.sum('lines_deleted')
    )

    joined = changed_files_df.join(
        diffs_grouped, on=['commit_hash', 'changed_file_id'], how='left'
    )

    errors = joined.filter(
        (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
    )

    # allow a bit of wiggle room as line change counts can be different for
    # `git log shortstat` and `git log -p`
    assert len(errors) / len(joined) < 0.01, (
        'Changed files and diffs do not match: ' + repr(errors.to_dicts())
    )


if __name__ == '__main__':
    pytest.main(__file__)
