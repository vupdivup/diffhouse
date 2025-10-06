import re
import subprocess
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from tempfile import TemporaryFile
from typing import Generator, Literal

import packaging.version

from .constants import MINIMUM_GIT_VERSION, PACKAGE_NAME


class GitCLI:
    """An abstraction that runs git commands in a local directory."""

    def __init__(self, cwd: str):
        """Initialize the git CLI.

        Args:
            cwd (str): Working directory for the git commands.

        """
        self._cwd = Path(cwd).absolute()

        if not self._cwd.exists():
            raise FileNotFoundError(f'Directory {self._cwd} does not exist.')

        if not self._cwd.is_dir():
            raise NotADirectoryError(f'Path {self._cwd} is not a directory.')

        self._version = self.get_version()

        if self.version < packaging.version.parse(MINIMUM_GIT_VERSION):
            raise GitError(
                f'Git version {MINIMUM_GIT_VERSION} or higher required. '
                + f'Current version: {self.version}.'
            )

    @contextmanager
    def run(self, *args: str) -> Generator[StringIO, None, None]:
        """Run a git command and stream its outputs.

        Use this function as a context manager.

        Args:
            *args: Arguments for the git command. The `git` keyword is
                automatically prepended.

        Returns:
            f: A string stream containing the command's standard output.

        """
        with TemporaryFile(
            'w+', encoding='utf-8', errors='replace', prefix=PACKAGE_NAME
        ) as f:
            try:
                subprocess.run(
                    ['git', *args],
                    check=True,
                    cwd=self._cwd,
                    stdout=f,
                )

                # move cursor to beginning for read
                f.seek(0)

                yield f

            except FileNotFoundError:
                raise EnvironmentError('Git is not installed or not in PATH.')
            except subprocess.CalledProcessError as e:
                raise GitError(e.stderr)
            finally:
                f.close()  # maybe unnecessary?

    def get_version(self) -> packaging.version.Version:
        """Get installed git version via `git --version`."""
        with self.run('--version') as out:
            output = out.read()
        v = re.match(r'git version (\d+\.\d+\.\d+)', output).group(1)
        return packaging.version.parse(v)

    @property
    def version(self) -> packaging.version.Version:
        """Installed git version."""
        return self._version

    def ls_remote(self, what: Literal['branches', 'tags']) -> str:
        """Run `git ls-remote` in the working directory.

        Set `what` to either `branches` or `tags` to list the respective refs.
        """
        if (
            self.version < packaging.version.parse('2.46.0')
            and what == 'branches'
        ):
            # use the deprecated --heads option for < 2.46.0
            what = 'heads'

        with self.run('ls-remote', f'--{what}', '--refs') as out:
            return out.read()


class GitError(Exception):
    """Custom exception for git-related errors."""

    def __init__(self, stderr: str):
        """Initialize the exception.

        Args:
            stderr (str): Standard error output from the git command.

        """
        self.message = f'Git command failed with the following error:\n{stderr}'
        super().__init__(self.message)
