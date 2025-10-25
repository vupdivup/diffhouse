"""Git metadata extractors."""

from diffhouse.pipelines.branch_pipeline import extract_branches
from diffhouse.pipelines.commit_pipeline import extract_commits
from diffhouse.pipelines.diff_pipeline import extract_diffs
from diffhouse.pipelines.file_mod_pipeline import extract_file_mods
from diffhouse.pipelines.tag_pipeline import extract_tags

__all__ = [
    'extract_commits',
    'extract_file_mods',
    'extract_diffs',
    'extract_branches',
    'extract_tags',
]
