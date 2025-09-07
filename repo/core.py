import tempfile
import subprocess
import pandas as pd

from pathlib import Path
from io import StringIO

LOG_FORMAT_SPECIFIERS = {
    'commit_hash': '%H',
    'author_name': '%an',
    'author_email': '%ae',
    'author_date': '%ad',
    'committer_name': '%cn',
    'committer_email': '%ce',
    'committer_date': '%cd',
    'subject': '%s',
    'body': '%b'
}
LOG_COLUMNS = list(LOG_FORMAT_SPECIFIERS.keys())

LOG_COLUMN_SEPARATOR = chr(0x1f)
LOG_RECORD_SEPARATOR = chr(0x1e)

class Remote:
    """
    GitHub repository metadata.
    """
    def __init__(self, owner: str, name: str):
        self.owner = owner
        """Repository owner."""

        self.name = name
        """Repository name."""

        self.url = f'https://github.com/{owner}/{name}.git'
        """GitHub repository URL."""

        self.id = f'{self.owner}-{self.name}'
        """Unique identifier for the repository. Format: `{owner}-{name}`"""

    def clone(self):
        """
        Create a local clone of the repository.
        """
        return Clone(self)

class Clone:
    """
    Local bare clone of a git repository.
    
    Resides in a temporary directory. For proper cleanup, the class is
    implemented as a context manager and meant to be used in a `with` statement.
    """
    def __init__(self, remote: Remote):
        self.remote = remote
        """Remote metadata."""

    def __enter__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._path = Path(self._temp_dir.name)

        # run git clone
        subprocess.run([
            'git',
            'clone',
            '--bare',
            '--filter=blob:none',
            self.remote.url,
            self._path
        ])

        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp_dir.cleanup()

    def _get_log(self):
        # prepare git log command
        specifiers = LOG_COLUMN_SEPARATOR.join(
            LOG_FORMAT_SPECIFIERS.values()
        )
        pattern = f'{specifiers}{LOG_RECORD_SEPARATOR}'

        # run git log
        return subprocess.run(
            # format instead of tformat is important to skip the last newline
            # for proper pandas parsing
            ['git', 'log', f'--pretty=format:{pattern}', '--date=iso'],
            cwd=self._path,
            capture_output=True,
            encoding='utf-8'
        ).stdout

    def get_commits_df(self):
        """
        Get commit history as a pandas DataFrame via `git log`.
        """
        # process output into DataFrame
        log = self._get_log()
        buf = StringIO(log)
        df = pd.read_csv(
            buf, 
            sep=LOG_COLUMN_SEPARATOR,
            lineterminator=LOG_RECORD_SEPARATOR,
            engine='c', # for lineterminator to work
            header=None,
            names=LOG_COLUMNS
        )
        
        # parse dates, UTC for mixed timezones
        for col in ['author_date', 'committer_date']:
            df[col] = pd.to_datetime(df[col], utc=True)

        # trim all whitespace of string columns
        for col in df:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        return df
