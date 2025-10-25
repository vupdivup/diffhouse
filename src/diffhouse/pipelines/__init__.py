"""Git metadata extractors."""

from diffhouse.pipelines.branch_pipeline import extract_branches
from diffhouse.pipelines.commit_pipeline import extract_commits
from diffhouse.pipelines.diff_pipeline import extract_diffs
from diffhouse.pipelines.file_mod_pipeline import extract_filemods
from diffhouse.pipelines.tag_pipeline import extract_tags

__all__ = [
    'extract_commits',
    'extract_filemods',
    'extract_diffs',
    'extract_branches',
    'extract_tags',
]
