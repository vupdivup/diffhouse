import pandas as pd

from .cloning import TempClone
from .engine import get_remote_url, get_commits, get_branches, get_tags

class Repo:
    '''
    Represents a git repository.
    '''
    def __init__(self, url: str):
        '''
        Initialize the repository from remote at `url` and load metadata. This
        may take some time depending on the repository size.
        '''

        with TempClone(url, shallow=True) as c:
            # get normalized URL via git
            self._url = get_remote_url(c.path)

            self._commits = get_commits(c.path).assign(repository=self.url)

            self._branches = pd.DataFrame({
                'branch': get_branches(c.path),
                'repository': self.url})
            self._tags = pd.DataFrame({
                'tag': get_tags(c.path),
                'repository': self.url})

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

        Schema:
        | Column | Description |
        | --- | --- |
        | `commit_hash` | Full hash of the commit. |
        | `author_name` | Author username. |
        | `author_email` | Author email. |
        | `author_date` | Commit creation date. |
        | `committer_name` | Committer username. |
        | `committer_email` | Committer email. |
        | `committer_date` | Commit apply date. |
        | `subject` | Subject line of the commit message. |
        | `body` | Body of the commit message. |
        | `repository` | Remote repository URL. |
        '''
        return self._commits.copy()
    
    @property
    def branches(self) -> pd.DataFrame:
        '''
        Branches of the repository.

        Schema:
        | Column | Description |
        | --- | --- |
        | `branch` | Branch name. |
        | `repository` | Remote repository URL. |
        '''
        return self._branches.copy()
    
    @property
    def tags(self) -> pd.DataFrame:
        '''
        Tags of the repository.

        Schema:
        | Column | Description |
        | --- | --- |
        | `tag` | Tag name. |
        | `repository` | Remote repository URL. |
        '''
        return self._tags.copy()
