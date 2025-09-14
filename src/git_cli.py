import subprocess

from pathlib import Path

class GitCLI:
    """
    An abstraction that runs git commands in a local directory.
    """
    def __init__(self, cwd: str):
        """
        Initialize the git CLI.

        Args:
            cwd (str): Working directory for the git commands.
        """
        self._cwd = Path(cwd).absolute()

        if not self._cwd.exists():
            raise FileNotFoundError(f"Directory {self._cwd} does not exist.")
        
        if not self._cwd.is_dir():
            raise NotADirectoryError(f"Path {self._cwd} is not a directory.")
        
    def run(self, *args: str) -> str:
        """
        Run a git command.

        Args:
            *args (str): Arguments for the git command. The `git` keyword is
                automatically prepended.

        Returns:
            stdout (str): Standard text output of the git command.
        """
        try:
            return subprocess.run(
                ['git', *args],
                check=True,
                cwd=self._cwd,
                capture_output=True,
                encoding='utf-8'
            ).stdout
        except FileNotFoundError:
            raise EnvironmentError("Git is not installed or not in PATH.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed.\n{e.stderr}")
