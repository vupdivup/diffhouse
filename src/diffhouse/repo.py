import pandas as pd

from .cloning import SlimClone
from .engine import process_log

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
            self._commits = process_log(c.path)

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
