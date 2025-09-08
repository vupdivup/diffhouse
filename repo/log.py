import subprocess
import pandas as pd

from pathlib import Path
from io import StringIO

FORMAT_SPECIFIERS = {
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

COLUMNS = list(FORMAT_SPECIFIERS.keys())

COLUMN_SEPARATOR = chr(0x1f)
RECORD_SEPARATOR = chr(0x1e)

class Log:
    """
    Output of a `git log` command, executed in a local repository.
    """
    def __init__(self, path: str):
        """
        Populate the log cache by running `git log` in `path`.

        Args:
            path (str): Path to a local repository.
        """
        self._path = Path(path)

        if not self._path.exists():
            raise FileNotFoundError(f'Path {self._path} does not exist.')

        if not self._path.is_dir():
            raise NotADirectoryError(f'Path {self._path} is not a directory.')

        self._output = self._get_output()

    def _get_output(self):
        # prepare git log command
        specifiers = COLUMN_SEPARATOR.join(
            FORMAT_SPECIFIERS.values()
        )
        pattern = f'{specifiers}{RECORD_SEPARATOR}'

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
            sep=COLUMN_SEPARATOR,
            lineterminator=RECORD_SEPARATOR,
            engine='c', # for lineterminator to work
            header=None,
            names=COLUMNS
        )
        
        # parse dates, UTC for mixed timezones
        for col in ['author_date', 'committer_date']:
            df[col] = pd.to_datetime(df[col], utc=True)

        # trim all whitespace of string columns
        for col in df:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        return df
