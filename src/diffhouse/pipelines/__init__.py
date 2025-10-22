"""Git metadata extractors."""

from .branch_pipeline import extract_branches
from .commit_pipeline import stream_commits
from .diff_pipeline import stream_diffs
from .file_mod_pipeline import stream_changed_files
from .tag_pipeline import extract_tags

__all__ = [
    'stream_commits',
    'stream_changed_files',
    'stream_diffs',
    'extract_branches',
    'extract_tags',
]
