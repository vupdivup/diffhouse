import logging

import polars as pl
import pytest

from tests.fixtures import (  # noqa: F401
    commits__diffhouse,
    diffs__diffhouse,
    filemods__diffhouse,
    repo,
)

logger = logging.getLogger()


def test_commits_vs_filemods(
    commits__diffhouse: pl.DataFrame,  # noqa: F811
    filemods__diffhouse: pl.DataFrame,  # noqa: F811
) -> None:
    """Test overlaps of `repo.commits` and `repo.filemods`."""
    files_grouped = filemods__diffhouse.group_by('commit_hash').agg(
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
    # of file mods, so allow a bit of wiggle room
    assert len(errors) / len(joined) < 0.01, (
        'Commits and file mods do not match: ' + repr(errors.to_dicts())
    )


def test_filemods_vs_diffs(
    filemods__diffhouse: pl.DataFrame,  # noqa: F811
    diffs__diffhouse: pl.LazyFrame,  # noqa: F811
) -> None:
    """Test overlaps of `repo.filemods` and `repo.diffs`."""
    # using lazy loading as this is an expensive operation
    diffs_grouped = diffs__diffhouse.group_by('commit_hash', 'filemod_id').agg(
        pl.sum('lines_added'), pl.sum('lines_deleted')
    )

    joined = filemods__diffhouse.lazy().join(
        diffs_grouped, on=['commit_hash', 'filemod_id'], how='left'
    )

    joined_len = joined.select(pl.len()).collect().item()

    logger.info(f'Comparing {joined_len} file mods locally')

    errors = joined.filter(
        (pl.col('lines_added') != pl.col('lines_added_right'))
        | (pl.col('lines_deleted') != pl.col('lines_deleted_right'))
    ).collect()

    # allow a bit of wiggle room as line change counts can be different for
    # `git log shortstat` and `git log -p`
    assert len(errors) / joined_len < 0.01, (
        'File mods and diffs do not match: ' + repr(errors.to_dicts())
    )


if __name__ == '__main__':
    pytest.main(__file__)
