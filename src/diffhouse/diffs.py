import re

from collections.abc import Iterator

from .git import GitCLI
from .utils import hash
from .constants import RECORD_SEPARATOR

def get_diffs(path: str) -> Iterator[dict]:
    '''
    Get diffs per commit and file for local repository at `path`.
    '''
    log = _log_diffs(path)
    return _parse_diffs(log)

def _log_diffs(path: str, sep: str = RECORD_SEPARATOR) -> str:
    '''
    Run a variation of `git log -p` with commits delimited by `sep` and return
    the output.
    '''
    git = GitCLI(path)
    log = git.run('log', '-p', '-U0', f"--pretty=format:'{sep}%H'")
    return log

def _parse_diffs(
        log: str, sep: str = RECORD_SEPARATOR) -> Iterator[dict]:
    '''
    Parse the output of `log_diffs` (`log` parameter with separator `sep`) into
    a structured format.
    '''
    commits = log.split(sep)[1:]

    file_sep_pat = re.compile(r'^diff --git', flags=re.MULTILINE)
    filepaths_pat = re.compile(r'"?a/(.+)"? "?b/(.+)"?')
    hunk_header_pat = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",
        flags=re.MULTILINE)

    for commit in commits:
        commit_hash, body = commit.split('\n', 1)
        files = re.split(file_sep_pat, body)[1:]
        for file in files:
            # format: a/path b/path
            header = file.split('\n', 1)[0]

            path_before, path_after = re.search(filepaths_pat, header) \
                .groups()
            hunks_raw = re.split(hunk_header_pat, file)[1:]

            # zip hunk header data with content
            hunks_grouped = tuple(
                {
                    'start_line_before': int(hunks_raw[i]),
                    'line_count_before': int(hunks_raw[i + 1] or 1),
                    'start_line_after': int(hunks_raw[i + 2]),
                    'line_count_after': int(hunks_raw[i + 3] or 1),
                    'content': hunks_raw[i + 4].split('\n', 1)[1]
                }
                for i in range(0, len(hunks_raw), 5)
            )

            for hunk in hunks_grouped:
                lines = hunk['content'].splitlines()
                additions = [line[1:] for line in lines if line.startswith('+')]
                deletions = [line[1:] for line in lines if line.startswith('-')]

                yield {
                    'revision_id': hash(commit_hash, path_before, path_after),
                    'start_line_before': hunk['start_line_before'],
                    'line_count_before': hunk['line_count_before'],
                    'start_line_after': hunk['start_line_after'],
                    'line_count_after': hunk['line_count_after'],
                    'additions': additions,
                    'deletions': deletions
                }
