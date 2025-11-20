"""Git operations wrapper for project repositories."""

from pathlib import Path
from typing import Union

from genesis_pantheon.logger import logger


class GitManager:
    """Thin wrapper around gitpython for project repository management."""

    def __init__(
        self,
        path: Union[str, Path],
        auto_init: bool = True,
    ) -> None:
        """Initialise the GitManager for the given path.

        Args:
            path: Directory to manage as a git repository.
            auto_init: If True, run ``git init`` when no repo exists.
        """
        try:
            import git as gitpython
        except ImportError as exc:
            raise ImportError(
                "gitpython is required for GitManager. "
                "Install it with: pip install gitpython"
            ) from exc
        self._git = gitpython
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        if auto_init and not (self.path / ".git").exists():
            self._repo = gitpython.Repo.init(str(self.path))
            logger.debug(f"Initialised git repo at {self.path}")
        elif (self.path / ".git").exists():
            self._repo = gitpython.Repo(str(self.path))
        else:
            self._repo = None

    @property
    def repo(self):
        """Return the underlying gitpython Repo object."""
        return self._repo

    def stage_all(self) -> None:
        """Stage all changes in the working tree.

        Raises:
            RuntimeError: If no git repo is available.
        """
        if self._repo is None:
            raise RuntimeError("No git repository available.")
        self._repo.git.add(A=True)
        logger.debug(f"Staged all changes in {self.path}")

    def commit(self, message: str) -> None:
        """Create a commit with the given message.

        If there is nothing to commit the operation is skipped silently.

        Args:
            message: Commit message string.
        """
        if self._repo is None:
            return
        try:
            if self._repo.is_dirty(untracked_files=True):
                self.stage_all()
                self._repo.index.commit(message)
                logger.debug(f"Committed: {message!r}")
            else:
                logger.debug("Nothing to commit, skipping.")
        except Exception as exc:
            logger.warning(f"Git commit failed: {exc}")

    def get_changed_files(self) -> list[str]:
        """Return a list of changed file paths (relative to repo root).

        Returns:
            List of file path strings.
        """
        if self._repo is None:
            return []
        try:
            changed = [
                item.a_path
                for item in self._repo.index.diff(None)
            ]
            untracked = list(self._repo.untracked_files)
            return changed + untracked
        except Exception as exc:
            logger.warning(f"Could not get changed files: {exc}")
            return []


__all__ = ["GitManager"]
