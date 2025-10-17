"""Git metadata extractors."""

from .branch_pipeline import get_branches
from .changed_file_pipeline import stream_changed_files
from .commit_pipeline import stream_commits
from .diff_pipeline import stream_diffs
from .tag_pipeline import get_tags

__all__ = [
    'stream_commits',
    'stream_changed_files',
    'stream_diffs',
    'get_branches',
    'get_tags',
]
