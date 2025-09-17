import pandas as pd

from .cloning import SlimClone
from .engine import get_remote_url, get_commits, get_branches, get_tags

class Repo:
    '''
    Represents a git repository.
    '''
    def __init__(self, url: str):
        '''
        Initialize the repository and load metadata. This may take some time
        depending on the repository size.

        Args:
            url (str): URL of the repository.
        '''

        with SlimClone(url) as c:
            # get normalized URL via git
            self._url = get_remote_url(c.path)

            self._commits = get_commits(c.path).assign(repository=self.url)
            self._branches = get_branches(c.path).assign(repository=self.url)
            self._tags = get_tags(c.path).assign(repository=self.url)

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
