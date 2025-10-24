from collections.abc import Iterator
from contextlib import contextmanager
from io import StringIO

import regex

from ..entities import Commit
from ..git import GitCLI
from .constants import RECORD_SEPARATOR, UNIT_SEPARATOR
from .utils import safe_iter, split_stream

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


def extract_commits(path: str, shortstats: bool = False) -> Iterator[Commit]:
    """Stream main branch commits from a git repository.

    Args:
        path: Path to the git repository.
        shortstats: Whether to include shortstat information.

    Yields:
        Commit objects.

    """
    with log_commits(path, shortstats=shortstats) as log:
        yield from safe_iter(
            parse_commits(log, parse_shortstats=shortstats),
            'Failed to parse commit. Skipping...',
        )


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


def tweak_git_iso_datetime(dt: str) -> str:
    """Convert git ISO datetime to precise ISO 8601 format.

    Args:
        dt: Git ISO datetime string (*YYYY-MM-DD HH:MM:SS ±HHMM*).

    Returns:
        ISO 8601 formatted datetime string (*YYYY-MM-DDTHH:MM:SS±HH:MM*).

    """
    return dt[:10] + 'T' + dt[11:19] + dt[20:23] + ':' + dt[23:25]


def parse_commits(
    log: StringIO,
    field_sep: str = UNIT_SEPARATOR,
    record_sep: str = RECORD_SEPARATOR,
    parse_shortstats: bool = False,
) -> Iterator[Commit]:
    """Parse the output of `log_commits`."""
    source_prefix_rgx = regex.compile(
        r'^refs\/(?:remotes\/origin|tags|heads)\/'
    )
    files_changed_pat = regex.compile(r'(\d+) file')
    insertions_pat = regex.compile(r'(\d+) insertion')
    deletions_pat = regex.compile(r'(\d+) deletion')

    commits = split_stream(log, record_sep, chunk_size=10_000)
    next(commits)  # skip first empty record

    for commit in commits:
        values = commit.split(field_sep)

        # match all fields with field names except the shortstat section
        fields = dict(zip(FIELDS, values[:-1], strict=True))

        source = source_prefix_rgx.sub('', fields['source'])

        if parse_shortstats:
            shortstat = values[-1]

            files_changed_match = files_changed_pat.search(shortstat)
            insertions_match = insertions_pat.search(shortstat)
            deletions_match = deletions_pat.search(shortstat)

            files_changed = (
                int(files_changed_match.group(1)) if files_changed_match else 0
            )

            insertions = (
                int(insertions_match.group(1)) if insertions_match else 0
            )
            deletions = int(deletions_match.group(1)) if deletions_match else 0

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

        yield Commit(
            commit_hash=fields['commit_hash'],
            source=source,
            is_merge=is_merge,
            parents=parents,
            author_name=fields['author_name'],
            author_email=fields['author_email'],
            author_date=tweak_git_iso_datetime(fields['author_date']),
            committer_name=fields['committer_name'],
            committer_email=fields['committer_email'],
            committer_date=tweak_git_iso_datetime(fields['committer_date']),
            message_subject=message_subject,
            message_body=message_body,
            files_changed=files_changed,
            lines_added=insertions,
            lines_deleted=deletions,
        )
