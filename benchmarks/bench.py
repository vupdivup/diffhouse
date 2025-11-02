import argparse
import sys

import pyperf
from pydriller import Repository as PydrillerRepo

from diffhouse import Repo as DiffhouseRepo


def get_commits__diffhouse(url: str) -> None:
    """Iterate over commits and commit attributes using diffhouse."""
    with DiffhouseRepo(url) as r:
        for c in r.commits:
            c.commit_hash  # noqa: B018
            c.author_name  # noqa: B018
            c.author_email  # noqa: B018
            c.author_date  # noqa: B018
            c.committer_name  # noqa: B018
            c.committer_email  # noqa: B018
            c.date  # noqa: B018
            c.message_subject  # noqa: B018
            c.message_body  # noqa: B018

            c.lines_added  # noqa: B018
            c.lines_deleted  # noqa: B018
            c.files_changed  # noqa: B018

            c.parents  # noqa: B018
            c.is_merge  # noqa: B018
            c.in_main  # noqa: B018


def get_files__diffhouse(url: str) -> None:
    """Iterate over modified files and their attributes using diffhouse."""
    with DiffhouseRepo(url) as r:
        for f in r.filemods:
            f.path_a  # noqa: B018
            f.path_b  # noqa: B018
            f.change_type  # noqa: B018
            f.lines_added  # noqa: B018
            f.lines_deleted  # noqa: B018


def get_diffs__diffhouse(url: str) -> None:
    """Iterate over diffs and their attributes using diffhouse."""
    with DiffhouseRepo(url) as r:
        for d in r.diffs:
            d.additions  # noqa: B018
            d.deletions  # noqa: B018


def get_commits__pydriller(url: str) -> None:
    """Iterate over commits and their attributes using PyDriller."""
    for c in PydrillerRepo(url).traverse_commits():
        c.hash  # noqa: B018
        c.author.email  # noqa: B018
        c.author.name  # noqa: B018
        c.author_date  # noqa: B018
        c.committer.email  # noqa: B018
        c.committer.name  # noqa: B018
        c.committer_date  # noqa: B018
        c.msg  # noqa: B018

        c.insertions  # noqa: B018
        c.deletions  # noqa: B018
        c.files  # noqa: B018

        c.parents  # noqa: B018
        c.merge  # noqa: B018
        c.in_main_branch  # noqa: B018


def get_files__pydriller(url: str) -> None:
    """Iterate over modified files and their attributes using PyDriller."""
    for c in PydrillerRepo(url).traverse_commits():
        for f in c.modified_files:
            f.old_path  # noqa: B018
            f.new_path  # noqa: B018
            f.change_type  # noqa: B018
            f.added_lines  # noqa: B018
            f.deleted_lines  # noqa: B018


def get_diffs__pydriller(url: str) -> None:
    """Iterate over diff attributes using PyDriller."""
    for c in PydrillerRepo(url).traverse_commits():
        for f in c.modified_files:
            f.diff_parsed  # noqa: B018


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Benchmark for comparing diffhouse and PyDriller'
    )
    parser.add_argument('--url', help='Repository URL to benchmark')
    args, unknown = parser.parse_known_args()
    url = args.url

    sys.argv = [sys.argv[0]] + unknown
    runner = pyperf.Runner(
        add_cmdline_args=lambda cmd, args: cmd.extend(['--url', url])  # noqa: ARG005
    )

    runner.bench_func(
        f'diffhouse | {url} | commits', get_commits__diffhouse, url
    )
    runner.bench_func(f'diffhouse | {url} | files', get_files__diffhouse, url)
    runner.bench_func(f'diffhouse | {url} | diffs', get_diffs__diffhouse, url)

    runner.bench_func(
        f'PyDriller | {url} | commits', get_commits__pydriller, url
    )
    runner.bench_func(f'PyDriller | {url} | files', get_files__pydriller, url)
    runner.bench_func(f'PyDriller | {url} | diffs', get_diffs__pydriller, url)
