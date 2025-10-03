import re
from collections.abc import Iterator
from dataclasses import dataclass

from ..git import GitCLI
from .constants import RECORD_SEPARATOR
from .utils import hash


@dataclass
class ChangedFile:
    """Snapshot of a file that was modified in a specific commit."""

    commit_hash: str
    """Full hash of the commit."""
    path_a: str
    """Path to file before the commit."""
    path_b: str
    """
    Path to file after the commit.
    
    Differs from `path_a` for renames and copies.
    """
    changed_file_id: str
    """
    Unique record identifier hashed from `commit_hash`, `path_a`, and `path_b`.
    """
    change_type: str
    """
    Single-letter code representing the change type. 
    
    See [git-status](https://git-scm.com/docs/git-status#_short_format) for
    possible values.
    """
    similarity: int
    """
    Similarity index between the two file versions.
    
    `0`-`100` for renames and copies, `100` otherwise.
    """
    lines_added: int
    """Number of lines added to the file in the commit."""
    lines_deleted: int
    """Number of lines deleted from the file in the commit."""


def collect_changed_files(path: str) -> Iterator[ChangedFile]:
    """Get changed files per commit for local repository at `path`."""
    name_statuses = list(parse_name_statuses(log_name_statuses(path)))
    numstats = list(parse_numstats(log_numstats(path)))

    # TODO: optimize
    index = {n['changed_file_id']: n for n in name_statuses}

    for numstat in numstats:
        if numstat['changed_file_id'] in index:
            name_status = index[numstat['changed_file_id']]
            yield ChangedFile(
                commit_hash=name_status['commit_hash'],
                path_a=name_status['path_a'],
                path_b=name_status['path_b'],
                changed_file_id=name_status['changed_file_id'],
                change_type=name_status['change_type'],
                similarity=name_status['similarity'],
                lines_added=numstat['lines_added'],
                lines_deleted=numstat['lines_deleted'],
            )


def log_name_statuses(path: str, sep: str = RECORD_SEPARATOR) -> str:
    """Return the output of `git log --name-status` for a local repository.

    Args:
        path (str): Path to the local git repository.
        sep (str): Record separator between commits.

    """
    git = GitCLI(path)
    return git.run('log', f'--pretty=format:{sep}%H', '--name-status')


def parse_name_statuses(
    log: str, sep: str = RECORD_SEPARATOR
) -> Iterator[ChangedFile]:
    """Parse the output of `log_name_statuses`."""
    commits = log.split(sep)[1:]

    for c in commits:
        lines = c.strip().split('\n')
        commit_hash = lines[0]

        for line in lines[1:]:
            items = line.split('\t')
            change_type = items[0][0]

            if change_type in ['R', 'C']:
                similarity = int(items[0][1:])
                path_b = items[2]
                path_a = items[1]
            else:
                similarity = 100
                path_b = items[1]
                path_a = path_b

            yield {
                'commit_hash': commit_hash,
                'path_a': path_a,
                'path_b': path_b,
                'changed_file_id': hash(commit_hash, path_a, path_b),
                'change_type': change_type,
                'similarity': similarity,
            }


def log_numstats(path: str, sep: str = RECORD_SEPARATOR) -> str:
    """Return the output of `git log --numstat` for a local repository at `path`."""
    git = GitCLI(path)
    return git.run('log', f'--pretty=format:{sep}%H', '--numstat')


def parse_numstats(log: str, sep: str = RECORD_SEPARATOR) -> Iterator[dict]:
    """Parse the output of `log_numstats`."""
    commits = log.split(sep)[1:]

    for c in commits:
        lines = c.splitlines()
        commit_hash = lines[0]

        for line in lines[1:]:
            if line == '':
                continue

            items = [i for i in line.split('\t')]
            lines_added = 0 if items[0] == '-' else int(items[0])
            lines_deleted = 0 if items[1] == '-' else int(items[1])

            file_expr = items[2]

            if '{' in file_expr:
                # ../../{a => b}
                # ../{ => a}/..
                path_a = re.sub(r'\{(.*) => .*\}', r'\1', file_expr).replace(
                    '//', '/'
                )
                path_b = re.sub(r'\{.* => (.*)\}', r'\1', file_expr).replace(
                    '//', '/'
                )
            else:
                # ../../a => ../../b
                match = re.match(r'(.+) => (.+)', file_expr)
                path_a = match.group(1) if match else file_expr
                path_b = match.group(2) if match else file_expr

            yield {
                'changed_file_id': hash(commit_hash, path_a, path_b),
                'lines_added': lines_added,
                'lines_deleted': lines_deleted,
            }
