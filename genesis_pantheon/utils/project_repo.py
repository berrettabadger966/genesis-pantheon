"""Project file system management for GenesisPantheon."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from genesis_pantheon.logger import logger
from genesis_pantheon.utils.common import aread, awrite
from genesis_pantheon.utils.git_ops import GitManager

if TYPE_CHECKING:
    from genesis_pantheon.schema import Document


class FileRepository:
    """Manages files inside a specific subdirectory of a project."""

    def __init__(
        self,
        git_manager: GitManager | None,
        relative_path: Path,
        root: Path,
    ) -> None:
        self._git = git_manager
        self._rel = relative_path
        self._root = root
        self._abs = root / relative_path
        self._abs.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        """Absolute path to this repository directory."""
        return self._abs

    async def save(
        self,
        filename: str,
        content: str,
        dependencies: set | None = None,
    ) -> Document:
        """Write content to a file and return a Document.

        Args:
            filename: Relative filename within this repository.
            content: Text content to write.
            dependencies: Ignored; kept for API compatibility.

        Returns:
            Document representing the saved file.
        """
        from genesis_pantheon.schema import Document

        target = self._abs / filename
        await awrite(target, content)
        logger.debug(f"Saved {target}")
        return Document(
            root_path=str(self._abs),
            filename=filename,
            content=content,
        )

    async def get(self, filename: str) -> Document | None:
        """Read a file and return a Document, or None if missing.

        Args:
            filename: Relative filename within this repository.

        Returns:
            Document or None.
        """
        from genesis_pantheon.schema import Document

        target = self._abs / filename
        if not target.exists():
            return None
        content = await aread(target)
        return Document(
            root_path=str(self._abs),
            filename=filename,
            content=content,
        )

    async def get_all(self) -> list[Document]:
        """Return Document objects for every file in this repository.

        Returns:
            List of Document instances.
        """
        from genesis_pantheon.schema import Document

        docs: list[Document] = []
        for fp in sorted(self._abs.rglob("*")):
            if fp.is_file():
                rel = str(fp.relative_to(self._abs))
                content = await aread(fp)
                docs.append(
                    Document(
                        root_path=str(self._abs),
                        filename=rel,
                        content=content,
                    )
                )
        return docs

    async def get_changed_since(
        self, dependency: str
    ) -> list[Document]:
        """Return files changed since a given dependency string.

        Currently returns all files; a real implementation would
        use git diff with the dependency as a ref.

        Args:
            dependency: Git ref or file path (informational).

        Returns:
            List of changed Document instances.
        """
        return await self.get_all()


class ProjectRepository:
    """Top-level project file system with typed subdirectories."""

    def __init__(
        self,
        path: str | Path,
        git_init: bool = True,
    ) -> None:
        self._root = Path(path)
        self._root.mkdir(parents=True, exist_ok=True)
        self._git: GitManager | None = None
        if git_init:
            try:
                self._git = GitManager(self._root, auto_init=True)
            except ImportError:
                logger.warning(
                    "gitpython not available; git tracking disabled."
                )

    @property
    def root(self) -> Path:
        """Root directory of the project."""
        return self._root

    @property
    def docs(self) -> FileRepository:
        """Repository for documentation files."""
        return FileRepository(self._git, Path("docs"), self._root)

    @property
    def resources(self) -> FileRepository:
        """Repository for resource files."""
        return FileRepository(
            self._git, Path("resources"), self._root
        )

    @property
    def src(self) -> FileRepository:
        """Repository for source code files."""
        return FileRepository(self._git, Path("src"), self._root)

    @property
    def tests(self) -> FileRepository:
        """Repository for test files."""
        return FileRepository(self._git, Path("tests"), self._root)

    def get_repo(self, name: str) -> FileRepository:
        """Get a named sub-repository, creating it if needed.

        Args:
            name: Relative directory name.

        Returns:
            FileRepository for that directory.
        """
        return FileRepository(self._git, Path(name), self._root)

    def get_changed_files(self) -> dict[str, list[str]]:
        """Return changed files grouped by directory.

        Returns:
            Dict mapping directory name to list of changed files.
        """
        if self._git is None:
            return {}
        changed = self._git.get_changed_files()
        grouped: dict[str, list[str]] = {}
        for fp in changed:
            parts = Path(fp).parts
            key = parts[0] if len(parts) > 1 else "root"
            grouped.setdefault(key, []).append(fp)
        return grouped

    def commit_all(self, message: str = "Auto-commit by GenesisPantheon") -> None:
        """Stage and commit all current changes.

        Args:
            message: Commit message.
        """
        if self._git:
            self._git.commit(message)


__all__ = ["FileRepository", "ProjectRepository"]
