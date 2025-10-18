import logging

import polars as pl
import pytest

from .fixtures import (  # noqa: F401
    changed_files__diffhouse,
    commits__diffhouse,
    diffs__diffhouse,
    repo,
)

logger = logging.getLogger()


def test_commits_vs_changed_files(
    commits__diffhouse: pl.DataFrame,  # noqa: F811
    changed_files__diffhouse: pl.DataFrame,  # noqa: F811
) -> None:
    """Test that overlapping data of `repo.commits` and `repo.changed_files` matches."""
    files_grouped = changed_files__diffhouse.group_by('commit_hash').agg(
        pl.len().alias('files_changed'),
        pl.col('lines_added').sum().alias('lines_added'),
        pl.col('lines_deleted').sum().alias('lines_deleted'),
    )

    joined = commits__diffhouse.join(
        files_grouped, on='commit_hash', how='left', coalesce=False
    ).fill_nan(0)

    logger.info(f'Comparing {len(joined)} commits locally')

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
    changed_files__diffhouse: pl.DataFrame,  # noqa: F811
    diffs__diffhouse: pl.LazyFrame,  # noqa: F811
) -> None:
    """Test that overlapping data of `repo.changed_files` and `repo.diffs` matches."""
    # using lazy loading as this is an expensive operation
    diffs_grouped = diffs__diffhouse.group_by(
        'commit_hash', 'changed_file_id'
    ).agg(pl.sum('lines_added'), pl.sum('lines_deleted'))

    joined = changed_files__diffhouse.lazy().join(
        diffs_grouped, on=['commit_hash', 'changed_file_id'], how='left'
    )

    joined_len = joined.select(pl.len()).collect().item()

    logger.info(f'Comparing {joined_len} changed files locally')

    errors = joined.filter(
        (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
    ).collect()

    # allow a bit of wiggle room as line change counts can be different for
    # `git log shortstat` and `git log -p`
    assert len(errors) / joined_len < 0.01, (
        'Changed files and diffs do not match: ' + repr(errors.to_dicts())
    )


if __name__ == '__main__':
    pytest.main(__file__)
