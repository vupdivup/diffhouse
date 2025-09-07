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
        """
        Initialize remote via GitHub owner and repository name.
        Args:
            owner (str): Repository owner.
            name (str): Repository name.
        """
        self._owner = owner
        self._name = name
        self._url = f'https://github.com/{owner}/{name}.git'
        self._id = f'{owner}-{name}'

    @property
    def owner(self):
        """Repository owner."""
        return self._owner

    @property
    def name(self):
        """Repository name."""
        return self._name
    
    @property
    def url(self):
        """GitHub repository URL."""
        return self._url
    
    @property
    def id(self):
        """Unique identifier for the repository. Format: `{owner}-{name}`"""
        return self._id

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
        """
        Create a local clone of the GitHub repository.

        Args:
            remote (Remote): Remote to clone.
        """
        self._remote = remote

    @property
    def remote(self):
        """GitHub remote."""
        return self._remote

    @property
    def log(self):
        """Commit log of the repository."""
        return self._log

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

        # init log
        self._log = Log(self._path)

        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp_dir.cleanup()
    
class Log():
    """
    Output of a `git log` command, executed in a local repository.
    """
    def __init__(self, path: Path):
        """
        Populate the log cache by running `git log` in `path`.

        Args:
            path (Path): Path to a local repository.
        """
        self._path = path

        self._output = self._get_output()

    def _get_output(self):
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

    def to_df(self):
        """
        Get commit log as a pandas DataFrame.
        """
        # process output into DataFrame
        buf = StringIO(self._output)
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
