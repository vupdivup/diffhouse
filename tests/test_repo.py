import unittest
import os
import pandas as pd

from src.diffhouse import Repo

VALID_URL = 'https://github.com/vupdivup/diffhouse.git'
INVALID_URL = 'yh8sxKcLRFS14zEa6PvNNPaGMzZA3l'
CWD = os.getcwd()

class TestRepo(unittest.TestCase):
    def assert_valid_commit_history(self, repo: Repo):
        # type
        self.assertTrue(isinstance(repo.commits, pd.DataFrame))
        # non-empty dataframe
        self.assertFalse(repo.commits.empty)
        # null rows
        self.assertTrue(
            len(repo.commits.replace("", pd.NA)
                .dropna(how='all')) == len(repo.commits)
        )
        # commit_hash primary key
        self.assertTrue(    
            len(repo.commits['commit_hash'].dropna()) == len(repo.commits)
        )

    def test_remote(self):
        r = Repo(VALID_URL)
        self.assert_valid_commit_history(r)

    def test_local(self):
        r = Repo(CWD)
        self.assert_valid_commit_history(r)
        
    def test_invalid_url(self):
        with self.assertRaises(Exception):
            Repo(INVALID_URL)

if __name__ == '__main__':
    unittest.main()