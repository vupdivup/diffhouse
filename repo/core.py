import tempfile
import subprocess
import pandas as pd

from pathlib import Path
from io import StringIO

class Repo:
    """
    GitHub repository metadata.
    """
    def __init__(self, url: str):
        self.url = url
        """Git repository URL"""

        self.owner = self.url.split('/')[-2]
        """Repository owner"""

        self.name = self.url.split('/')[-1].replace('.git', '')
        """Repository name"""

        self.id = f'{self.owner}-{self.name}'
        """Unique identifier for the repository. Format: `{owner}-{name}`"""

    def clone(self):
        """
        Create a local clone of the repository.
        """
        return Clone(self)

class Clone:
    """
    Local clone of a git repository.
    
    Resides in a temporary directory. For proper cleanup, the class is
    implemented as a context manager and meant to be used in a `with` statement.
    """
    _LOG_FORMAT_SPECIFIERS = {
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

    _LOG_COLUMNS = list(_LOG_FORMAT_SPECIFIERS.keys())

    _LOG_COLUMN_DELIMITER = chr(0x1f)
    _LOG_RECORD_DELIMITER = chr(0x1e)

    def __init__(self, repo: Repo):
        self.repo = repo
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
            self.repo.url,
            self._path
        ])

        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp_dir.cleanup()

    def get_commits(self):
        """
        Get commit history as a pandas DataFrame via `git log`.
        """
        # prepare git log command
        specifiers = self._LOG_COLUMN_DELIMITER.join(
            self._LOG_FORMAT_SPECIFIERS.values()
        )
        pattern = f'{specifiers}{self._LOG_RECORD_DELIMITER}'

        # run git log
        log = subprocess.run(
            ['git', 'log', f'--pretty=tformat:{pattern}', '--date=iso'],
            cwd=self._path,
            capture_output=True,
            encoding='utf-8'
        )

        # process output into DataFrame
        buf = StringIO(log.stdout)
        df = pd.read_csv(
            buf, 
            sep=self._LOG_COLUMN_DELIMITER,
            lineterminator=self._LOG_RECORD_DELIMITER,
            engine='c', # for lineterminator to work
            header=None,
            names=self._LOG_COLUMNS
        )
        
        # parse dates, UTC for mixed timezones
        for col in ['author_date', 'committer_date']:
            df[col] = pd.to_datetime(df[col], utc=True)

        # trim all whitespace of string columns
        for col in df:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        return df
