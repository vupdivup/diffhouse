import logging
import re
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from tempfile import TemporaryFile
from typing import Literal

import packaging.version

from diffhouse.api.exceptions import GitError
from diffhouse.constants import MINIMUM_GIT_VERSION, PACKAGE_NAME

logger = logging.getLogger(__name__)


class GitCLI:
    """An abstraction that runs git commands in a local directory."""

    def __init__(self, cwd: str):
        """Initialize the git CLI.

        Args:
            cwd: Working directory for the git commands.

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
    def run(self, *args: str) -> Iterator[StringIO]:
        """Run a git command and stream its outputs.

        Use this function as a context manager.

        Args:
            *args: Arguments for the git command. The `git` keyword is
                automatically prepended.

        Yields:
            f: A string stream containing the command's standard output.

        Raises:
            EnvironmentError: If git is not installed or not in PATH.
            GitError: If the git command fails.

        """
        with TemporaryFile(
            'w+', encoding='utf-8', errors='replace', prefix=f'{PACKAGE_NAME}_'
        ) as f:
            logger.debug(
                f"Piping '{' '.join(['git', *args])}' command to {f.name}"
            )

            try:
                subprocess.run(
                    ['git', *args],
                    check=True,
                    cwd=self._cwd,
                    stdout=f,
                    stderr=subprocess.PIPE,  # to suppress console output
                )

                # move cursor to beginning for read
                f.seek(0)

                yield f

            except FileNotFoundError as e:
                raise EnvironmentError(
                    'Git is not installed or not in PATH.'
                ) from e
            except subprocess.CalledProcessError as e:
                raise GitError(e.stderr) from e
            finally:
                f.close()  # maybe unnecessary?

    def get_version(self) -> packaging.version.Version:
        """Get installed git version via `git --version`.

        Returns:
            Parsed git version.

        """
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

        Args:
            what: Specify whether to list branches or tags.

        Returns:
            List of refs as a string.

        """
        if (
            self.version < packaging.version.parse('2.46.0')
            and what == 'branches'
        ):
            # use the deprecated --heads option for < 2.46.0
            what = 'heads'

        with self.run('ls-remote', f'--{what}', '--refs') as out:
            return out.read()
