"""Tests for genesis_pantheon.chronicle module."""

from __future__ import annotations

from genesis_pantheon.chronicle import Chronicle
from genesis_pantheon.schema import Signal


def _make_signal(
    content: str,
    cause_by: str = "UserDirective",
    role: str = "user",
) -> Signal:
    return Signal(content=content, cause_by=cause_by, role=role)


class TestChronicle:
    def test_add_signal(self) -> None:
        c = Chronicle()
        sig = _make_signal("hello")
        c.add(sig)
        assert c.count() == 1
        assert c.storage[0] is sig

    def test_add_batch(self) -> None:
        c = Chronicle()
        sigs = [_make_signal(f"msg-{i}") for i in range(5)]
        c.add_batch(sigs)
        assert c.count() == 5

    def test_get_all(self) -> None:
        c = Chronicle()
        for i in range(4):
            c.add(_make_signal(f"msg-{i}"))
        result = c.get()
        assert len(result) == 4

    def test_get_recent_k(self) -> None:
        c = Chronicle()
        for i in range(10):
            c.add(_make_signal(f"msg-{i}"))
        result = c.get(k=3)
        assert len(result) == 3
        assert result[-1].content == "msg-9"

    def test_get_by_role(self) -> None:
        c = Chronicle()
        c.add(_make_signal("user msg", role="user"))
        c.add(_make_signal("assistant msg", role="assistant"))
        users = c.get_by_role("user")
        assert len(users) == 1
        assert users[0].content == "user msg"

    def test_get_by_actions(self) -> None:
        c = Chronicle()
        c.add(_make_signal("prd", cause_by="DraftVision"))
        c.add(_make_signal("design", cause_by="DesignSystem"))
        c.add(_make_signal("code", cause_by="CraftCode"))
        result = c.get_by_actions({"DraftVision", "CraftCode"})
        contents = {s.content for s in result}
        assert "prd" in contents
        assert "code" in contents
        assert "design" not in contents

    def test_try_recall_keyword(self) -> None:
        c = Chronicle()
        c.add(_make_signal("Python is great"))
        c.add(_make_signal("JavaScript too"))
        c.add(_make_signal("Love Python"))
        result = c.try_recall("python")
        assert len(result) == 2

    def test_try_recall_no_match(self) -> None:
        c = Chronicle()
        c.add(_make_signal("hello world"))
        result = c.try_recall("golang")
        assert result == []

    def test_clear(self) -> None:
        c = Chronicle()
        for i in range(5):
            c.add(_make_signal(f"msg-{i}"))
        c.clear()
        assert c.count() == 0
        assert c.storage == []

    def test_count(self) -> None:
        c = Chronicle()
        assert c.count() == 0
        c.add(_make_signal("one"))
        assert c.count() == 1

    def test_latest_returns_none_when_empty(self) -> None:
        c = Chronicle()
        assert c.latest() is None

    def test_latest_returns_last_signal(self) -> None:
        c = Chronicle()
        c.add(_make_signal("first"))
        c.add(_make_signal("last"))
        assert c.latest().content == "last"

    def test_index_built_correctly(self) -> None:
        c = Chronicle()
        c.add(_make_signal("a", cause_by="DraftVision"))
        c.add(_make_signal("b", cause_by="DraftVision"))
        assert len(c.index["DraftVision"]) == 2
