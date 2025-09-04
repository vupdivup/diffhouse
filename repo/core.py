import tempfile
import subprocess
import pandas as pd

from pathlib import Path

class Repo:
    """
    Represents a git repository cloned from GitHub.
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

    def __init__(self, url: str):
        self.url = url
        """Git repository URL"""

        self.owner = self.url.split('/')[-2]
        """Repository owner"""

        self.name = self.url.split('/')[-1].replace('.git', '')
        """Repository name"""

        self.id = f'{self.owner}-{self.name}'
        """Unique identifier for the repository. Format: `{owner}-{name}`"""

    def __enter__(self):
        self._temp_dir = tempfile.TemporaryDirectory(prefix='repo_')
        self._path = Path(self._temp_dir.name)
        self._clone_path = self._path / 'repo'
        self._log_path = self._path / 'logs' / f'{self.id}.txt'

        self._clone(path=self._clone_path)
        self._log_commits()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._temp_dir.cleanup()
    
    def _clone(self, path: str):
        # TODO: error handling
        subprocess.run([
            'git', 'clone', '--bare', '--filter=blob:none', self.url, path
            ])

    def _log_commits(self):
        # create log directory
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        # prepare git log command
        specifiers = self._LOG_COLUMN_DELIMITER.join(
            self._LOG_FORMAT_SPECIFIERS.values()
            )
        pattern = f'{specifiers}{self._LOG_RECORD_DELIMITER}'

        with open(self._log_path, 'w') as f:
            subprocess.run(
                ['git', 'log', f'--pretty=tformat:{pattern}', '--date=iso'],
                cwd=self._clone_path, stdout=f
                )
        
    def get_commits(self) -> pd.DataFrame:
        """
        Returns a DataFrame of main branch commits.
        """
        commits = pd.read_csv(
            self._log_path, 
            sep=self._LOG_COLUMN_DELIMITER,
            lineterminator=self._LOG_RECORD_DELIMITER,
            engine='c', # for lineterminator to work
            header=None,
            names=self._LOG_COLUMNS
            )
        
        # parse dates, UTC for mixed timezones
        for col in ['author_date', 'committer_date']:
            commits[col] = pd.to_datetime(commits[col], utc=True)

        # trim all whitespace of string columns
        for col in commits:
            if commits[col].dtype == 'object':
                commits[col] = commits[col].str.strip()

        return commits
