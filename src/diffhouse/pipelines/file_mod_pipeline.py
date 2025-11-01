import logging
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from io import StringIO

import regex

from diffhouse.api.exceptions import ParserWarning
from diffhouse.entities import FileMod
from diffhouse.git import GitCLI
from diffhouse.pipelines.constants import RECORD_SEPARATOR
from diffhouse.pipelines.utils import fast_hash_64, split_stream

logger = logging.getLogger(__name__)

NUMSTAT_PATH_A_RGX = regex.compile(r'\{(.*) => .*\}')
NUMSTAT_PATH_B_RGX = regex.compile(r'\{.* => (.*)\}')


def extract_filemods(path: str) -> Iterator[FileMod]:
    """Get file modifications per commit for a local git repository.

    Args:
        path: Path to the local git repository.

    Yields:
        Objects for each file changed in each commit.

    """
    # Have to read numstat into memory for join
    # Can experiment with sorting beforehand to see if it's faster
    logger.info('Extracting file modifications')
    logger.debug('Logging numstats')

    with log_numstats(path) as log:
        logger.debug('Parsing numstats')
        # create index for joining with name-statuses
        index = {n['filemod_id']: n for n in parse_numstats(log)}

        logger.debug(f'Parsed {len(index)} numstat records')

    logger.debug('Logging name-statuses')
    with log_name_statuses(path) as log:
        logger.debug('Joining name-statuses with numstats')

        for name_status in parse_name_statuses(log):
            if name_status['filemod_id'] in index:
                numstat = index[name_status['filemod_id']]

                yield FileMod(
                    commit_hash=name_status['commit_hash'],
                    path_a=name_status['path_a'],
                    path_b=name_status['path_b'],
                    filemod_id=name_status['filemod_id'],
                    change_type=name_status['change_type'],
                    similarity=name_status['similarity'],
                    lines_added=numstat['lines_added'],
                    lines_deleted=numstat['lines_deleted'],
                )

    logger.debug('Extracted all file modifications')


@contextmanager
def log_name_statuses(
    path: str, sep: str = RECORD_SEPARATOR
) -> Iterator[StringIO]:
    """Return the output of `git log --name-status` for a local repository as a string stream.

    Args:
        path: Path to the local git repository.
        sep: Record separator between commits.

    Yields:
        A string stream containing the log output.

    """
    git = GitCLI(path)
    with git.run(
        'log', f'--pretty=format:{sep}%H', '--name-status', '--all'
    ) as out:
        try:
            yield out
        finally:
            out.close()


def parse_name_statuses(
    log: StringIO, sep: str = RECORD_SEPARATOR
) -> Iterator[dict]:
    """Parse the output of `log_name_statuses`.

    Args:
        log: The log output as a string stream.
        sep: Separator between commits.

    Yields:
        A dictionary containing the parsed name-status information for each
        changed file.

    """
    commits = split_stream(log, sep, 10_000)
    next(commits)  # skip first empty record

    for commit in commits:
        try:
            lines = commit.strip().split('\n')
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
                    'filemod_id': fast_hash_64(commit_hash, path_a, path_b),
                    'change_type': change_type,
                    'similarity': similarity,
                }
        except Exception:
            warnings.warn(
                'Skipping malformed file modification record.',
                ParserWarning,
                stacklevel=2,
            )
            logger.warning(
                f'Skipping malformed name-status record: {repr(commit)}',
                exc_info=True,
            )


@contextmanager
def log_numstats(path: str, sep: str = RECORD_SEPARATOR) -> Iterator[StringIO]:
    """Return the output of `git log --numstat` for a local repository as a string stream.

    Args:
        path: Path to the local git repository.
        sep: Record separator between commits.

    Yields:
        A string stream containing the log output.

    """
    git = GitCLI(path)
    with git.run(
        'log', f'--pretty=format:{sep}%H', '--numstat', '--all'
    ) as out:
        try:
            yield out
        finally:
            out.close()


def parse_numstats(
    log: StringIO, sep: str = RECORD_SEPARATOR
) -> Iterator[dict]:
    """Parse the output of `log_numstats`.

    Args:
        log: The log output as a string.
        sep: Record separator between commits.

    Yields:
        A dictionary containing the parsed numstat information for each changed
            file.

    """
    commits = split_stream(log, sep, 10_000)
    next(commits)  # skip first empty record

    for commit in commits:
        try:
            lines = commit.splitlines()
            commit_hash = lines[0]

            for line in lines[1:]:
                if line == '':
                    continue

                items = line.split('\t')
                lines_added = 0 if items[0] == '-' else int(items[0])
                lines_deleted = 0 if items[1] == '-' else int(items[1])

                file_expr = items[2]

                if '{' in file_expr:
                    # ../../{a => b}
                    # ../{ => a}/..
                    path_a = NUMSTAT_PATH_A_RGX.sub(r'\1', file_expr).replace(
                        '//', '/'
                    )
                    path_b = NUMSTAT_PATH_B_RGX.sub(r'\1', file_expr).replace(
                        '//', '/'
                    )
                else:
                    # ../../a => ../../b
                    # NOTE: technically => can be in a unix filename
                    paths = file_expr.split(' => ')
                    path_a = paths[0]
                    path_b = paths[1] if len(paths) > 1 else file_expr

                yield {
                    'filemod_id': fast_hash_64(commit_hash, path_a, path_b),
                    'lines_added': lines_added,
                    'lines_deleted': lines_deleted,
                }
        except Exception:
            warnings.warn(
                'Skipping malformed file modification record.',
                ParserWarning,
                stacklevel=2,
            )
            logger.warning(
                f'Skipping malformed numstat record: {repr(commit)}',
                exc_info=True,
            )
