"""Workspace configuration for project file management."""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class WorkspaceConfig(BaseModel):
    """Configuration for the project workspace directory."""

    path: Path = Field(
        default_factory=lambda: Path.home() / ".genesis_pantheon" / "workspace"
    )
    auto_archive: bool = True
    use_git: bool = True
    git_reinit: bool = False
    encoding: str = "utf-8"
    project_name: str = ""

    @field_validator("path", mode="before")
    @classmethod
    def _resolve_path(cls, v: object) -> Path:
        return Path(str(v)).expanduser().resolve()

    def project_path(self, project_name: str = "") -> Path:
        """Return the full path for a named project.

        Args:
            project_name: Optional project name override.

        Returns:
            Resolved project directory path.
        """
        name = project_name or self.project_name
        if name:
            return self.path / name
        return self.path

    def ensure_exists(self) -> None:
        """Create the workspace directory if it does not exist."""
        self.path.mkdir(parents=True, exist_ok=True)


__all__ = ["WorkspaceConfig"]
