import pandas as pd

from .slim_clone import SlimClone
from .engine import process_log

class Repo:
    def __init__(self, url: str):
        self._url = url

        with SlimClone(url) as c:
            self._commits = process_log(c.path)

    @property
    def url(self):
        """URL of the remote repository."""
        return self._url
    
    @property
    def commits(self) -> pd.DataFrame:
        """Commit log as a pandas DataFrame."""
        return self._commits.copy()
