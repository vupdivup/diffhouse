import logging
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from io import StringIO

import regex  # runs super fast for the complex diff patterns compared to re

from diffhouse.api.exceptions import ParserWarning
from diffhouse.entities import Diff
from diffhouse.git import GitCLI
from diffhouse.pipelines.constants import RECORD_SEPARATOR
from diffhouse.pipelines.utils import fast_hash_64, split_stream

logger = logging.getLogger(__name__)

FILE_SEP_RGX = regex.compile(r'^diff --git', flags=regex.MULTILINE)
FILEPATHS_RGX = regex.compile(r'"?a/(.+)"? "?b/(.+)"?')
HUNK_HEADER_RGX = regex.compile(
    r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', flags=regex.MULTILINE
)


def extract_diffs(path: str) -> Iterator[Diff]:
    """Stream diffs per commit and file for a local repository.

    Args:
        path: Path to the local git repository.

    Yields:
        Diff objects.

    """
    logger.info('Extracting diffs')
    logger.debug('Logging diffs')

    with log_diffs(path) as log:
        logger.debug('Parsing diffs')
        yield from parse_diffs(log)

    logger.debug('Extracted all diffs')


@contextmanager
def log_diffs(path: str, sep: str = RECORD_SEPARATOR) -> Iterator[StringIO]:
    """Run a variation of `git log -p` and return the output as a string stream.

    Args:
        path: Path to the local repository.
        sep: Separator between commits.

    Yields:
        A string stream containing the git log with diffs.

    """
    git = GitCLI(path)
    with git.run(
        'log', '-p', '-U0', f'--pretty=format:{sep}%H', '--all'
    ) as log:
        try:
            yield log
        finally:
            log.close()


def parse_diffs(log: StringIO, sep: str = RECORD_SEPARATOR) -> Iterator[Diff]:
    """Parse the output of `log_diffs`.

    Args:
        log: A string stream containing the git log with diffs.
        sep: Separator between commits.

    Yields:
        Diff objects.

    """
    # note: need big chunk size as diffs can be >1MB
    commits = split_stream(log, sep, chunk_size=10_000_000)
    next(commits)  # skip first empty record

    for commit in commits:
        try:
            parts = commit.split('\n', 1)
            commit_hash = parts[0]

            # ignore empty commits
            if len(parts) == 1:
                continue

            files = FILE_SEP_RGX.split(parts[1])[1:]
            for file in files:
                # format: a/path b/path, both quoted if having misc chars
                header = file.split('\n', 1)[0]

                path_a, path_b = FILEPATHS_RGX.search(header).groups()
                hunks_raw = HUNK_HEADER_RGX.split(file)[1:]

                # zip hunk header data with content
                hunks_grouped = tuple(
                    {
                        'start_a': int(hunks_raw[i]),
                        'length_a': int(hunks_raw[i + 1] or 1),
                        'start_b': int(hunks_raw[i + 2]),
                        'length_b': int(hunks_raw[i + 3] or 1),
                        'content': hunks_raw[i + 4].split('\n', 1)[1],
                    }
                    for i in range(0, len(hunks_raw), 5)
                )

                for hunk in hunks_grouped:
                    lines = hunk['content'].splitlines()

                    additions = []
                    deletions = []

                    for line in lines:
                        if line.startswith('+'):
                            additions.append(line[1:])
                        elif line.startswith('-'):
                            deletions.append(line[1:])

                    lines_added = len(additions)
                    lines_deleted = len(deletions)

                    yield Diff(
                        commit_hash=commit_hash,
                        path_a=path_a,
                        path_b=path_b,
                        filemod_id=fast_hash_64(commit_hash, path_a, path_b),
                        start_a=hunk['start_a'],
                        length_a=hunk['length_a'],
                        start_b=hunk['start_b'],
                        length_b=hunk['length_b'],
                        lines_added=lines_added,
                        lines_deleted=lines_deleted,
                        additions=additions,
                        deletions=deletions,
                    )
        except Exception:
            warnings.warn(
                'Skipping malformed diff record', ParserWarning, stacklevel=2
            )
            logger.warning(
                f'Skipping malformed diff record: {repr(commit)}',
                exc_info=True,
            )
