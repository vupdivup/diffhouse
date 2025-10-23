"""Git metadata extractors."""

from .branch_pipeline import extract_branches
from .commit_pipeline import stream_commits
from .diff_pipeline import stream_diffs
from .file_mod_pipeline import stream_file_mods
from .tag_pipeline import extract_tags

__all__ = [
    'stream_commits',
    'stream_file_mods',
    'stream_diffs',
    'extract_branches',
    'extract_tags',
]
