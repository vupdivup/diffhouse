import unittest
import pandas as pd

from src.diffhouse import Repo

VALID_URL = 'https://github.com/pola-rs/polars.git'
INVALID_URL = 'yh8sxKcLRFS14zEa6PvNNPaGMzZA3l'

class TestRepo(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(VALID_URL)

    def assert_valid_df(self, df: pd.DataFrame):
        # type
        self.assertTrue(isinstance(df, pd.DataFrame))
        # non-empty dataframe
        self.assertFalse(df.empty)
        # null rows
        self.assertTrue(
            len(df.replace("", pd.NA).dropna(how='all')) == len(df)
        )

    def assert_primary_key(self, df: pd.DataFrame, col: str):
        self.assertTrue(col in df.columns)
        self.assertTrue(df[col].notna().all())
        self.assertTrue(df[col].is_unique)

    def test_commits(self):
        self.assert_valid_df(self.repo.commits)
        self.assert_primary_key(self.repo.commits, 'commit_hash')

    def test_branches(self):
        self.assert_valid_df(self.repo.branches)
        self.assert_primary_key(self.repo.branches, 'branch')

    def test_tags(self):
        self.assert_valid_df(self.repo.tags)
        self.assert_primary_key(self.repo.tags, 'tag')

    def test_source_col(self):
        for df in [self.repo.commits, self.repo.branches, self.repo.tags]:
            self.assertTrue('repository' in df.columns)

    def test_invalid_url(self):
        with self.assertRaises(Exception):
            Repo(INVALID_URL)

if __name__ == '__main__':
    unittest.main()
