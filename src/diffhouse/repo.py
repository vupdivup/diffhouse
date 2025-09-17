import pandas as pd

from .cloning import SlimClone
from .engine import get_commits, get_branches, get_tags

class Repo:
    '''
    Represents a git repository.
    '''
    def __init__(self, url: str):
        '''
        Initialize the repository and load commit history.

        Args:
            url (str): URL of the repository.
        '''
        self._url = url

        with SlimClone(url) as c:
            self._commits = get_commits(c.path)
            self._branches = get_branches(c.path)
            self._tags = get_tags(c.path)

    @property
    def url(self):
        '''
        URL of the remote repository.
        '''
        return self._url
    
    @property
    def commits(self) -> pd.DataFrame:
        '''
        Commit history as a pandas DataFrame.
        '''
        return self._commits.copy()
    
    @property
    def branches(self) -> pd.DataFrame:
        '''
        Branches of the repository.
        '''
        return self._branches.copy()
    
    @property
    def tags(self) -> pd.DataFrame:
        '''
        Tags of the repository.
        '''
        return self._tags.copy()
