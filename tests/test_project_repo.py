"""Tests for ProjectRepository and FileRepository."""

from __future__ import annotations

from genesis_pantheon.utils.project_repo import (
    FileRepository,
    ProjectRepository,
)


class TestFileRepository:
    def test_path_property_returns_absolute_path(
        self, tmp_path
    ) -> None:
        repo = FileRepository(None, tmp_path.name, tmp_path.parent)
        assert repo.path.exists()

    def test_creates_directory_on_init(self, tmp_path) -> None:
        subdir = tmp_path / "new_subdir"
        assert not subdir.exists()
        FileRepository(None, subdir.name, tmp_path)
        assert subdir.exists()

    async def test_save_creates_file(self, tmp_path) -> None:
        repo = FileRepository(None, tmp_path.name, tmp_path.parent)
        doc = await repo.save("hello.txt", "Hello, World!")
        target = repo.path / "hello.txt"
        assert target.exists()
        assert target.read_text() == "Hello, World!"
        assert doc.filename == "hello.txt"
        assert doc.content == "Hello, World!"

    async def test_get_returns_document(self, tmp_path) -> None:
        repo = FileRepository(None, tmp_path.name, tmp_path.parent)
        (repo.path / "data.txt").write_text("some data")
        doc = await repo.get("data.txt")
        assert doc is not None
        assert doc.content == "some data"

    async def test_get_returns_none_for_missing_file(
        self, tmp_path
    ) -> None:
        repo = FileRepository(None, tmp_path.name, tmp_path.parent)
        doc = await repo.get("nonexistent.txt")
        assert doc is None

    async def test_get_all_returns_all_files(self, tmp_path) -> None:
        repo = FileRepository(None, tmp_path.name, tmp_path.parent)
        (repo.path / "a.txt").write_text("aaa")
        (repo.path / "b.txt").write_text("bbb")
        docs = await repo.get_all()
        filenames = [d.filename for d in docs]
        assert "a.txt" in filenames
        assert "b.txt" in filenames

    async def test_get_all_empty_directory(self, tmp_path) -> None:
        repo = FileRepository(None, tmp_path.name, tmp_path.parent)
        docs = await repo.get_all()
        assert docs == []

    async def test_get_changed_since_returns_all_files(
        self, tmp_path
    ) -> None:
        repo = FileRepository(None, tmp_path.name, tmp_path.parent)
        (repo.path / "f.txt").write_text("content")
        docs = await repo.get_changed_since("HEAD~1")
        assert len(docs) == 1


class TestProjectRepository:
    def test_creates_root_directory(self, tmp_path) -> None:
        project = tmp_path / "myproject"
        _ = ProjectRepository(project, git_init=False)
        assert project.exists()

    def test_root_property(self, tmp_path) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        assert repo.root.name == "p"

    def test_docs_property_returns_file_repository(
        self, tmp_path
    ) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        assert isinstance(repo.docs, FileRepository)
        assert (tmp_path / "p" / "docs").exists()

    def test_src_property_returns_file_repository(
        self, tmp_path
    ) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        assert isinstance(repo.src, FileRepository)
        assert (tmp_path / "p" / "src").exists()

    def test_tests_property_returns_file_repository(
        self, tmp_path
    ) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        assert isinstance(repo.tests, FileRepository)

    def test_resources_property_returns_file_repository(
        self, tmp_path
    ) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        assert isinstance(repo.resources, FileRepository)

    def test_get_repo_creates_custom_subdirectory(
        self, tmp_path
    ) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        custom = repo.get_repo("custom_dir")
        assert isinstance(custom, FileRepository)
        assert (tmp_path / "p" / "custom_dir").exists()

    def test_get_changed_files_without_git_returns_empty(
        self, tmp_path
    ) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        result = repo.get_changed_files()
        assert result == {}

    def test_commit_all_without_git_does_not_raise(
        self, tmp_path
    ) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        repo.commit_all("test commit")  # should not raise

    async def test_save_and_retrieve_file(self, tmp_path) -> None:
        repo = ProjectRepository(tmp_path / "p", git_init=False)
        _ = await repo.src.save("main.py", "print('hello')")
        retrieved = await repo.src.get("main.py")
        assert retrieved is not None
        assert retrieved.content == "print('hello')"
