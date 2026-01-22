"""Tests for genesis_pantheon.schema module."""

from __future__ import annotations

import pytest

from genesis_pantheon.constants import SIGNAL_ROUTE_TO_ALL
from genesis_pantheon.schema import (
    CodingContext,
    Document,
    Documents,
    RunCodeResult,
    Signal,
    SignalQueue,
)


class TestSignal:
    def test_signal_creates_unique_id(self) -> None:
        s1 = Signal(content="hello")
        s2 = Signal(content="world")
        assert s1.id != s2.id
        assert len(s1.id) == 32  # UUID hex

    def test_signal_defaults_to_broadcast(self) -> None:
        s = Signal(content="test")
        assert SIGNAL_ROUTE_TO_ALL in s.send_to

    def test_signal_cause_by_defaults_to_user_directive(self) -> None:
        s = Signal(content="test")
        assert s.cause_by == "UserDirective"

    def test_signal_cause_by_accepts_string(self) -> None:
        s = Signal(content="test", cause_by="DraftVision")
        assert s.cause_by == "DraftVision"

    def test_signal_cause_by_accepts_class(self) -> None:
        class DummyDirective:
            __name__ = "DummyDirective"

        s = Signal(content="test", cause_by=DummyDirective)
        assert s.cause_by == "DummyDirective"

    def test_signal_send_to_serializes_as_list(self) -> None:
        s = Signal(content="test", send_to={"Alice", "Bob"})
        serialized = s.model_dump()
        assert isinstance(serialized["send_to"], list)

    def test_signal_content_required(self) -> None:
        with pytest.raises(Exception):
            Signal()  # type: ignore[call-arg]

    def test_signal_send_to_string_becomes_set(self) -> None:
        s = Signal(content="test", send_to="Alice")
        assert isinstance(s.send_to, set)
        assert "Alice" in s.send_to

    def test_signal_send_to_list_becomes_set(self) -> None:
        s = Signal(content="test", send_to=["Alice", "Bob"])
        assert isinstance(s.send_to, set)
        assert "Alice" in s.send_to

    def test_signal_is_for_broadcast(self) -> None:
        s = Signal(content="test")
        assert s.is_for("Anyone")

    def test_signal_is_for_specific_name(self) -> None:
        s = Signal(content="test", send_to={"Alice"})
        assert s.is_for("Alice")
        assert not s.is_for("Bob")

    def test_signal_sent_from_normalises_none(self) -> None:
        s = Signal(content="test", sent_from=None)
        assert s.sent_from == ""


class TestSignalQueue:
    async def test_push_and_get(self) -> None:
        q = SignalQueue()
        sig = Signal(content="queued")
        q.push(sig)
        result = await q.get()
        assert result.content == "queued"

    async def test_pop_all_clears_queue(self) -> None:
        q = SignalQueue()
        for i in range(3):
            q.push(Signal(content=f"msg-{i}"))
        popped = q.pop_all()
        assert len(popped) == 3
        assert q.empty

    async def test_put_is_async(self) -> None:
        q = SignalQueue()
        sig = Signal(content="async-put")
        await q.put(sig)
        assert not q.empty

    def test_empty_initially(self) -> None:
        q = SignalQueue()
        assert q.empty

    async def test_pop_all_empty_returns_empty_list(self) -> None:
        q = SignalQueue()
        result = q.pop_all()
        assert result == []


class TestDocument:
    def test_root_relative_path(self) -> None:
        doc = Document(
            root_path="/project/src", filename="main.py", content="..."
        )
        assert "main.py" in doc.root_relative_path
        assert "src" in doc.root_relative_path

    def test_root_relative_path_no_root(self) -> None:
        doc = Document(filename="main.py", content="x = 1")
        assert doc.root_relative_path == "main.py"

    async def test_load_nonexistent_returns_none(
        self, tmp_path
    ) -> None:
        result = await Document.load("nonexistent.py", tmp_path)
        assert result is None

    async def test_load_existing_file(self, tmp_path) -> None:
        p = tmp_path / "test.py"
        p.write_text("x = 1")
        doc = await Document.load("test.py", tmp_path)
        assert doc is not None
        assert doc.content == "x = 1"
        assert doc.filename == "test.py"


class TestDocuments:
    def test_from_iterable(self) -> None:
        docs = [
            Document(filename="a.py", content="a"),
            Document(filename="b.py", content="b"),
        ]
        collection = Documents.from_iterable(docs)
        assert "a.py" in collection.docs
        assert "b.py" in collection.docs

    def test_empty_collection(self) -> None:
        collection = Documents()
        assert collection.docs == {}


class TestCodingContext:
    def test_coding_context_fields(self) -> None:
        ctx = CodingContext(filename="main.py")
        assert ctx.filename == "main.py"
        assert ctx.design_doc is None
        assert ctx.task_doc is None
        assert ctx.code_doc is None

    def test_coding_context_with_docs(self) -> None:
        doc = Document(filename="design.md", content="# Design")
        ctx = CodingContext(filename="main.py", design_doc=doc)
        assert ctx.design_doc is not None
        assert ctx.design_doc.content == "# Design"


class TestRunCodeResult:
    def test_success_property(self) -> None:
        r = RunCodeResult(summary="OK", stdout="done", returncode=0)
        assert r.success

    def test_failure_property(self) -> None:
        r = RunCodeResult(
            summary="Fail", stdout="error", returncode=1
        )
        assert not r.success
