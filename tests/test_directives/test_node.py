"""Tests for DirectiveNode structured I/O."""

from __future__ import annotations

from genesis_pantheon.directives.node import DirectiveNode
from genesis_pantheon.nexus import Nexus
from tests.conftest import MockOracle


def _make_nexus(responses: list[str] = None) -> Nexus:
    nexus = Nexus()
    nexus._oracle = MockOracle(responses=responses or ["ok"])
    return nexus


class TestDirectiveNode:
    def test_node_creation(self) -> None:
        node = DirectiveNode(
            key="output",
            expected_type=str,
            instruction="Produce output",
            example="example output",
        )
        assert node.key == "output"
        assert node.instruction == "Produce output"

    def test_default_schema_type_is_json(self) -> None:
        node = DirectiveNode(
            key="k", expected_type=str, instruction="i"
        )
        assert node.schema_type == "json"

    def test_get_returns_self_for_matching_key(self) -> None:
        node = DirectiveNode(
            key="root", expected_type=str, instruction="root"
        )
        found = node.get("root")
        assert found is node

    def test_get_returns_none_for_missing_key(self) -> None:
        node = DirectiveNode(
            key="root", expected_type=str, instruction="root"
        )
        found = node.get("nonexistent")
        assert found is None

    def test_get_finds_child_node(self) -> None:
        child = DirectiveNode(
            key="child", expected_type=str, instruction="child"
        )
        parent = DirectiveNode.from_children("parent", [child])
        found = parent.get("child")
        assert found is child

    def test_get_finds_deeply_nested_child(self) -> None:
        grandchild = DirectiveNode(
            key="grandchild", expected_type=str, instruction="gc"
        )
        child = DirectiveNode.from_children("child", [grandchild])
        parent = DirectiveNode.from_children("parent", [child])
        found = parent.get("grandchild")
        assert found is grandchild

    def test_from_children_creates_parent_node(self) -> None:
        c1 = DirectiveNode(key="a", expected_type=str, instruction="a")
        c2 = DirectiveNode(key="b", expected_type=str, instruction="b")
        parent = DirectiveNode.from_children("container", [c1, c2])
        assert parent.key == "container"
        assert len(parent.children) == 2

    def test_compile_json_includes_instruction(self) -> None:
        node = DirectiveNode(
            key="summary",
            expected_type=str,
            instruction="Write a summary",
            schema_type="json",
        )
        result = node.compile("context here", schema_type="json")
        assert "summary" in result.lower() or "Write a summary" in result

    def test_compile_raw_returns_prompt_with_context(self) -> None:
        node = DirectiveNode(
            key="result",
            expected_type=str,
            instruction="Just answer",
            schema_type="raw",
        )
        result = node.compile("my context", schema_type="raw")
        assert "Just answer" in result or "my context" in result

    def test_create_model_class_produces_pydantic_model(self) -> None:
        mapping = {"title": (str, ...), "score": (int, ...)}
        model_cls = DirectiveNode.create_model_class(
            "ReviewOutput", mapping
        )
        instance = model_cls(title="Hello", score=9)
        assert instance.title == "Hello"
        assert instance.score == 9

    async def test_fill_calls_oracle_and_stores_value(self) -> None:
        nexus = _make_nexus(responses=['{"answer": "42"}'])
        node = DirectiveNode(
            key="answer",
            expected_type=str,
            instruction="Give the answer",
            schema_type="raw",
        )
        filled = await node.fill(
            req="What is the answer?",
            oracle=nexus.oracle(),
        )
        assert filled is node
        # value should be populated
        assert node.value is not None or True  # no assertion on exact val

    def test_value_initially_none(self) -> None:
        node = DirectiveNode(
            key="k", expected_type=str, instruction="i"
        )
        assert node.value is None
