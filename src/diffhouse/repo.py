import pandas as pd
import logging

from .cloning import TempClone
from .engine import *

logger = logging.getLogger()

class Repo:
    '''
    Represents a git repository.
    '''
    def __init__(self, url: str, blobs: bool = False):
        '''
        Initialize the repository from remote at `url` and load metadata. This
        may take some time depending on the repository size.

        If `blobs` is `True`, fetch file-level metadata will as well. Note that
        this greatly increases processing time.
        '''
        self._blobs = blobs

        logger.info(f'Cloning {url}')
        with TempClone(url, shallow=not blobs) as c:
            # get normalized URL via git
            self._url = get_remote_url(c.path)

            logger.info('Extracting commits')
            self._commits = get_commits(c.path).assign(repository=self.url)

            logger.info('Extracting branches')
            self._branches = pd.DataFrame({
            'branch': get_branches(c.path),
            'repository': self.url})

            logger.info('Extracting tags')
            self._tags = pd.DataFrame({
            'tag': get_tags(c.path),
            'repository': self.url})

            
            if blobs:
                logger.info('Extracting diffs')
                self._status_changes = get_status_changes(c.path)
                self._line_changes = get_line_changes(c.path)

                self._diffs = pd.merge(
                    left=self._status_changes,
                    right=self._line_changes,
                    on=['commit_hash', 'file', 'from_file'],
                    how='inner',
                    suffixes=('_status', '_numstat'))
                
                self._diffs['repository'] = self.url

        logger.info('\033[92mDone\033[0m')

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
    
    @property
    def diffs(self) -> pd.DataFrame:
        '''
        File-level changes in the repository.

        Schema:
        | Column | Description |
        | --- | --- |
        | `commit_hash` | Full hash of the commit. |
        | `file` | Path to file. |
        | `status` | Single-letter code representing the change type. See [git-status](https://git-scm.com/docs/git-status#_short_format) for possible values. |
        | `from_file` | Path to file before the change, for renames and copies. |
        | `lines_added` | Number of lines added. |
        | `lines_deleted` | Number of lines deleted. |
        | `repository` | Remote repository URL. |
        '''
        if not self._blobs:
            raise ValueError(
                'Initialize Repo with `blobs`=`True` to load diffs.')

        return self._diffs.copy()
