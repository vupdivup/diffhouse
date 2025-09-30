import re

from dataclasses import dataclass
from collections.abc import Iterator

from ..git import GitCLI
from .utils import hash
from .constants import RECORD_SEPARATOR

# TODO: binary diffs


@dataclass
class Diff:
    """Changes made to a hunk of code in a specific commit."""

    commit_hash: str
    """Full hash of the commit."""
    path_a: str
    """Path to file before the commit."""
    path_b: str
    """Path to file after the commit."""
    revision_id: str
    """File revision ID."""
    start_a: int
    """Starting line number before the commit."""
    length_a: int
    """Line count before the commit."""
    start_b: int
    """Starting line number after the commit."""
    length_b: int
    """Line count after the commit."""
    additions: list[str]
    """Lines added."""
    deletions: list[str]
    """Lines deleted."""


def collect_diffs(path: str) -> list[Diff]:
    """
    Get diffs per commit and file for local repository at `path`.
    """
    log = _log_diffs(path)
    return list(_parse_diffs(log))


def _log_diffs(path: str, sep: str = RECORD_SEPARATOR) -> str:
    """
    Run a variation of `git log -p` with commits delimited by `sep` and return
    the output.
    """
    git = GitCLI(path)
    log = git.run("log", "-p", "-U0", f"--pretty=format:'{sep}%H'")
    return log


def _parse_diffs(log: str, sep: str = RECORD_SEPARATOR) -> Iterator[Diff]:
    """
    Parse the output of `log_diffs` (`log` parameter with separator `sep`) into
    a structured format.
    """
    commits = log.split(sep)[1:]

    file_sep_pat = re.compile(r"^diff --git", flags=re.MULTILINE)
    filepaths_pat = re.compile(r'"?a/(.+)"? "?b/(.+)"?')
    hunk_header_pat = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", flags=re.MULTILINE
    )

    for commit in commits:
        commit_hash, body = commit.split("\n", 1)
        files = re.split(file_sep_pat, body)[1:]
        for file in files:
            # format: a/path b/path
            header = file.split("\n", 1)[0]

            path_a, path_b = re.search(filepaths_pat, header).groups()
            hunks_raw = re.split(hunk_header_pat, file)[1:]

            # zip hunk header data with content
            hunks_grouped = tuple(
                {
                    "start_a": int(hunks_raw[i]),
                    "length_a": int(hunks_raw[i + 1] or 1),
                    "start_b": int(hunks_raw[i + 2]),
                    "length_b": int(hunks_raw[i + 3] or 1),
                    "content": hunks_raw[i + 4].split("\n", 1)[1],
                }
                for i in range(0, len(hunks_raw), 5)
            )

            for hunk in hunks_grouped:
                lines = hunk["content"].splitlines()
                additions = [line[1:] for line in lines if line.startswith("+")]
                deletions = [line[1:] for line in lines if line.startswith("-")]

                yield Diff(
                    commit_hash=commit_hash,
                    path_a=path_a,
                    path_b=path_b,
                    revision_id=hash(commit_hash, path_a, path_b),
                    start_a=hunk["start_a"],
                    length_a=hunk["length_a"],
                    start_b=hunk["start_b"],
                    length_b=hunk["length_b"],
                    # TODO: lines added and deleted metrics
                    additions=additions,
                    deletions=deletions,
                )
