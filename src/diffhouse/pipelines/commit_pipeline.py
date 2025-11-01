import logging
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from io import StringIO

import regex

from diffhouse.api.exceptions import ParserWarning
from diffhouse.entities import Commit
from diffhouse.git import GitCLI
from diffhouse.pipelines.constants import RECORD_SEPARATOR, UNIT_SEPARATOR
from diffhouse.pipelines.utils import parse_git_timestamp, split_stream

logger = logging.getLogger(__name__)

PRETTY_LOG_FORMAT_SPECIFIERS = {
    'commit_hash': '%H',
    'author_name': '%an',
    'author_email': '%ae',
    'author_date': '%ad',
    'committer_name': '%cn',
    'committer_email': '%ce',
    'committer_date': '%cd',
    # using raw body as the sanitized subject would remove single newlines
    'message': '%B',
    'parents': '%P',
    'source': '%S',
}

FIELDS = list(PRETTY_LOG_FORMAT_SPECIFIERS.keys())

SOURCE_PREFIX_RGX = regex.compile(r'^refs\/(?:remotes\/origin|tags|heads)\/')
FILES_CHANGED_RGX = regex.compile(r'(\d+) file')
INSERTIONS_RGX = regex.compile(r'(\d+) insertion')
DELETIONS_RGX = regex.compile(r'(\d+) deletion')


def extract_commits(path: str, shortstats: bool = False) -> Iterator[Commit]:
    """Stream main branch commits from a git repository.

    Args:
        path: Path to the git repository.
        shortstats: Whether to include shortstat information.

    Yields:
        Commit objects.

    """
    # lookup table to check if a commit is in main branch
    logger.info('Extracting commits')
    logger.debug('Indexing commits on main branch')

    main = dict.fromkeys(iter_hashes_on_main(path))

    logger.debug('Logging commits')
    with log_commits(path, shortstats=shortstats) as log:
        logger.debug('Parsing commits')
        for commit in parse_commits(log, parse_shortstats=shortstats):
            yield Commit(**commit, in_main=commit['commit_hash'] in main)

    logger.debug('Extracted all commits')


def iter_hashes_on_main(path: str) -> Iterator[str]:
    """Iterate over commit hashes from the default branch.

    Args:
        path: Path to the git repository.

    Yields:
        Commit hashes.

    """
    git = GitCLI(path)
    with git.run('log', '--pretty=format:%H') as log:
        yield from (line.strip() for line in log)


@contextmanager
def log_commits(
    path: str,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
    shortstats: bool = False,
) -> Iterator[StringIO]:
    """Return a structured git log as a string stream.

    Args:
        path: Path to the git repository.
        field_sep: Separator between fields in each commit.
        record_sep: Separator between commits.
        shortstats: Whether to include a shortstat summary of changes per
            commit.

    Yields:
        A string stream containing the git log.

    """
    # prepare git log command
    specifiers = field_sep.join(PRETTY_LOG_FORMAT_SPECIFIERS.values())

    pattern = f'{record_sep}{specifiers}{UNIT_SEPARATOR}'
    args = ['log', f'--pretty=format:{pattern}', '--date=iso', '--all']

    if shortstats:
        args.append('--shortstat')

    git = GitCLI(path)
    with git.run(*args) as log:
        try:
            yield log
        finally:
            log.close()


def parse_commits(
    log: StringIO,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
    parse_shortstats: bool = False,
) -> Iterator[Commit]:
    """Parse the output of `log_commits`."""
    commits = split_stream(log, record_sep, chunk_size=10_000)
    next(commits)  # skip first empty record

    for commit in commits:
        try:
            values = commit.split(field_sep)

            # match all fields with field names except the shortstat section
            fields = dict(zip(FIELDS, values[:-1], strict=True))

            source = SOURCE_PREFIX_RGX.sub('', fields['source'])

            date, date_local = parse_git_timestamp(fields['committer_date'])
            author_date, author_date_local = parse_git_timestamp(
                fields['author_date']
            )

            if parse_shortstats:
                shortstat = values[-1]

                files_changed_match = FILES_CHANGED_RGX.search(shortstat)
                insertions_match = INSERTIONS_RGX.search(shortstat)
                deletions_match = DELETIONS_RGX.search(shortstat)

                files_changed = (
                    int(files_changed_match.group(1))
                    if files_changed_match
                    else 0
                )

                insertions = (
                    int(insertions_match.group(1)) if insertions_match else 0
                )
                deletions = (
                    int(deletions_match.group(1)) if deletions_match else 0
                )

            else:
                files_changed = None
                insertions = None
                deletions = None

            if fields['parents'] == '':
                # first commit has no parents
                parents = []
            else:
                parents = fields['parents'].split(' ')

            # it's a merge commit if parents field has more than one hash
            is_merge = len(parents) > 1

            message_parts = fields['message'].split('\n\n', 1)
            message_subject = message_parts[0].strip()
            message_body = (
                message_parts[1].strip() if len(message_parts) > 1 else ''
            )

            yield {
                'commit_hash': fields['commit_hash'],
                'source': source,
                'is_merge': is_merge,
                'parents': parents,
                'date': date,
                'date_local': date_local,
                'author_name': fields['author_name'],
                'author_email': fields['author_email'],
                'author_date': author_date,
                'author_date_local': author_date_local,
                'committer_name': fields['committer_name'],
                'committer_email': fields['committer_email'],
                'message_subject': message_subject,
                'message_body': message_body,
                'files_changed': files_changed,
                'lines_added': insertions,
                'lines_deleted': deletions,
            }
        except Exception:
            # Handle exceptions related to string operations and field parsing
            warnings.warn(
                'Skipping malformed commit record', ParserWarning, stacklevel=2
            )
            logger.warning(
                f'Skipping malformed commit record: {repr(commit)}',
                exc_info=True,
            )
            continue
