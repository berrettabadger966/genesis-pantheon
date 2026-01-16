"""Tests for the Directive base class."""

from __future__ import annotations

import pytest

from genesis_pantheon.directives.base import Directive, DirectiveOutput
from genesis_pantheon.nexus import Nexus
from tests.conftest import MockOracle


class ConcreteDirective(Directive):
    """Minimal concrete directive for testing."""

    name: str = "ConcreteDirective"

    async def run(self, *args, **kwargs) -> DirectiveOutput:
        response = await self._ask("What should I do?")
        return DirectiveOutput(content=response)


class TestDirective:
    def _make_nexus(self, responses=None) -> Nexus:
        nexus = Nexus()
        nexus._oracle = MockOracle(
            responses=responses or ["test response"]
        )
        return nexus

    def test_name_defaults_to_class_name(self) -> None:
        d = ConcreteDirective()
        assert d.name == "ConcreteDirective"

    def test_name_can_be_overridden(self) -> None:
        d = ConcreteDirective(name="CustomName")
        assert d.name == "CustomName"

    def test_set_prefix_updates_prefix_field(self) -> None:
        nexus = self._make_nexus()
        d = ConcreteDirective()
        d.nexus = nexus
        d.set_prefix("You are a helpful assistant")
        assert d.prefix == "You are a helpful assistant"

    def test_set_prefix_returns_self_for_chaining(self) -> None:
        nexus = self._make_nexus()
        d = ConcreteDirective()
        d.nexus = nexus
        result = d.set_prefix("prefix")
        assert result is d

    async def test_ask_calls_oracle(self) -> None:
        nexus = self._make_nexus(responses=["oracle said this"])
        d = ConcreteDirective()
        d.nexus = nexus
        response = await d._ask("test prompt")
        assert response == "oracle said this"

    async def test_ask_with_system_msgs(self) -> None:
        nexus = self._make_nexus(responses=["sys response"])
        d = ConcreteDirective()
        d.nexus = nexus
        response = await d._ask(
            "prompt", system_msgs=["additional context"]
        )
        assert response == "sys response"

    async def test_run_calls_through_oracle(self) -> None:
        nexus = self._make_nexus(responses=["run result"])
        d = ConcreteDirective()
        d.nexus = nexus
        output = await d.run()
        assert output.content == "run result"

    async def test_run_raises_for_base_class(self) -> None:
        """Base Directive.run must raise NotImplementedError."""
        d = Directive()
        with pytest.raises(NotImplementedError):
            await d.run()

    def test_to_dict_and_from_dict(self) -> None:
        d = ConcreteDirective(desc="test directive")
        as_dict = d.to_dict()
        assert as_dict["name"] == "ConcreteDirective"
        assert as_dict["desc"] == "test directive"

    def test_from_dict_restores_instance(self) -> None:
        data = {"name": "ConcreteDirective", "desc": "restored"}
        d = ConcreteDirective.from_dict(data)
        assert d.name == "ConcreteDirective"
        assert d.desc == "restored"

    def test_set_prefix_without_nexus_does_not_raise(self) -> None:
        d = ConcreteDirective()
        # Should not raise even without nexus attached
        d.set_prefix("safe prefix")
        assert d.prefix == "safe prefix"
