"""SoftwareArena: specialised arena for software development."""

from __future__ import annotations

from pathlib import Path

from genesis_pantheon.arena.base import Arena
from genesis_pantheon.logger import logger
from genesis_pantheon.schema import Signal
from genesis_pantheon.utils.project_repo import ProjectRepository


class SoftwareArena(Arena):
    """Software development arena with project repository support.

    Extends :class:`Arena` with a :class:`ProjectRepository` for
    persisting generated code, documents, and tests to disk.
    """

    project_name: str = ""
    project_path: str = ""
    _repo: ProjectRepository | None = None

    def model_post_init(self, __context: object) -> None:
        """Initialise the project repository after model init."""
        super().model_post_init(__context)
        if self.project_path:
            self._repo = ProjectRepository(
                Path(self.project_path) / self.project_name,
                git_init=self.context.config.workspace.use_git,
            )
            logger.info(
                f"[SoftwareArena] Project repo at "
                f"{self.project_path}/{self.project_name}"
            )

    @property
    def repo(self) -> ProjectRepository | None:
        """The underlying project repository, or None.

        Returns:
            ProjectRepository instance or None.
        """
        return self._repo

    async def run(self) -> list[Signal]:
        """Execute one round and commit any new files to git.

        Returns:
            List of new signals produced this round.
        """
        new_signals = await super().run()
        if self._repo and new_signals:
            try:
                self._repo.commit_all(
                    f"Auto-commit: round produced "
                    f"{len(new_signals)} signal(s)"
                )
            except Exception as exc:
                logger.warning(
                    f"[SoftwareArena] Git commit failed: {exc}"
                )
        return new_signals

    def archive(self, auto: bool = True) -> None:
        """Archive arena state and commit final project snapshot.

        Args:
            auto: When True, commits any outstanding changes.
        """
        super().archive(auto)
        if auto and self._repo:
            try:
                self._repo.commit_all("Final auto-commit by GenesisPantheon")
            except Exception as exc:
                logger.warning(
                    f"[SoftwareArena] Final commit failed: {exc}"
                )


__all__ = ["SoftwareArena"]
