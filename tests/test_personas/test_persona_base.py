"""Tests for the Persona base agent class."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive, DirectiveOutput
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.personas.persona import (
    Persona,
    PersonaContext,
    PersonaReactMode,
)
from genesis_pantheon.schema import Signal
from tests.conftest import MockOracle


class EchoDirective(Directive):
    """Test directive that echoes its input."""

    name: str = "EchoDirective"

    async def run(self, *args, **kwargs) -> DirectiveOutput:
        ctx = kwargs.get("context", "default content")
        return DirectiveOutput(content=f"Echo: {ctx}")


class FailDirective(Directive):
    """Test directive that raises."""

    name: str = "FailDirective"

    async def run(self, *args, **kwargs) -> DirectiveOutput:
        raise RuntimeError("Intentional failure")


class EchoPersona(Persona):
    """Simple test persona using EchoDirective."""

    name: str = "EchoBot"
    profile: str = "Echo Agent"
    goal: str = "Echo everything"
    constraints: str = "None"


class TestPersonaContext:
    def test_initial_state_is_negative_one(self) -> None:
        ctx = PersonaContext()
        assert ctx.state == -1

    def test_initial_subscriptions_empty(self) -> None:
        ctx = PersonaContext()
        assert ctx.subscriptions == set()

    def test_relevant_signals_filters_by_subscription(self) -> None:
        ctx = PersonaContext()
        ctx.subscriptions = {"DraftVision"}

        s1 = Signal(content="a", cause_by="DraftVision")
        s2 = Signal(content="b", cause_by="CraftCode")
        ctx.chronicle.add(s1)
        ctx.chronicle.add(s2)

        relevant = ctx.relevant_signals
        assert len(relevant) == 1
        assert relevant[0].cause_by == "DraftVision"

    def test_history_returns_all_signals(self) -> None:
        ctx = PersonaContext()
        for i in range(3):
            ctx.chronicle.add(Signal(content=str(i)))
        assert len(ctx.history) == 3

    def test_react_mode_default(self) -> None:
        ctx = PersonaContext()
        assert ctx.react_mode == PersonaReactMode.REACT


class TestPersona:
    def _make_nexus(self) -> Nexus:
        nexus = Nexus()
        nexus._oracle = MockOracle(responses=["ok"])
        return nexus

    def test_subscribe_converts_to_str_set(self) -> None:
        p = EchoPersona()
        p._subscribe_to([EchoDirective, "SomeOther"])
        assert "EchoDirective" in p.ctx.subscriptions
        assert "SomeOther" in p.ctx.subscriptions

    def test_put_signal_adds_to_buffer(self) -> None:
        p = EchoPersona()
        s = Signal(content="hello")
        p.put_signal(s)
        # buffer should have one item
        items = p.ctx.signal_buffer.pop_all()
        assert len(items) == 1
        assert items[0].content == "hello"

    async def test_observe_filters_unsubscribed_signals(self) -> None:
        p = EchoPersona()
        p._subscribe_to([EchoDirective])
        p.put_signal(Signal(content="match", cause_by="EchoDirective"))
        p.put_signal(Signal(content="no match", cause_by="Other"))
        count = await p._observe()
        # Only the matching signal should be in news
        assert count == 1
        assert p.ctx.news[0].content == "match"

    async def test_observe_with_no_subscriptions_accepts_all(self) -> None:
        p = EchoPersona()
        # Empty subscriptions means accept all
        p.put_signal(Signal(content="any signal", cause_by="Anything"))
        count = await p._observe()
        assert count == 1

    async def test_think_returns_false_with_no_directives(self) -> None:
        p = EchoPersona()
        p.ctx.news = [Signal(content="x")]
        result = await p._think()
        assert result is False

    async def test_think_by_order_advances_state(self) -> None:
        p = EchoPersona()
        nexus = self._make_nexus()
        p.nexus = nexus
        p._assign_directives([EchoDirective])
        p.ctx.react_mode = PersonaReactMode.BY_ORDER
        has_action = await p._think()
        assert has_action is True
        assert p.ctx.state == 0

    async def test_think_by_order_stops_at_end(self) -> None:
        p = EchoPersona()
        nexus = self._make_nexus()
        p.nexus = nexus
        p._assign_directives([EchoDirective])
        p.ctx.react_mode = PersonaReactMode.BY_ORDER
        p.ctx.state = 0  # already at the only directive
        has_action = await p._think()
        assert has_action is False

    async def test_act_with_no_current_directive_returns_empty(self) -> None:
        p = EchoPersona()
        result = await p._act()
        assert result.content == ""

    async def test_act_with_directive_returns_signal(self) -> None:
        nexus = self._make_nexus()
        p = EchoPersona()
        p.nexus = nexus
        p._assign_directives([EchoDirective])
        p.ctx.news = [Signal(content="ping")]
        p._set_current_directive(p.directives[0])
        signal = await p._act()
        assert "Echo:" in signal.content
        assert signal.sent_from == "EchoBot"
        assert signal.cause_by == "EchoDirective"

    async def test_run_returns_none_when_buffer_empty(self) -> None:
        p = EchoPersona()
        result = await p.run()
        assert result is None

    async def test_run_processes_signal_in_react_mode(self) -> None:
        nexus = self._make_nexus()
        p = EchoPersona()
        p.nexus = nexus
        p._assign_directives([EchoDirective])
        p._subscribe_to([EchoDirective])
        s = Signal(content="test input", cause_by="EchoDirective")
        result = await p.run(signal=s)
        assert result is not None
        assert "Echo:" in result.content

    async def test_run_by_order_executes_all_directives(self) -> None:
        nexus = self._make_nexus()
        p = EchoPersona()
        p.nexus = nexus
        p._assign_directives([EchoDirective])
        p.ctx.react_mode = PersonaReactMode.BY_ORDER
        s = Signal(content="test", cause_by="UserDirective")
        result = await p.run(signal=s)
        assert result is not None

    def test_is_idle_when_buffer_and_news_empty(self) -> None:
        p = EchoPersona()
        assert p.is_idle is True

    def test_is_not_idle_when_signal_buffered(self) -> None:
        p = EchoPersona()
        p.put_signal(Signal(content="x"))
        assert p.is_idle is False

    def test_build_system_prompt_includes_profile_and_goal(self) -> None:
        p = EchoPersona()
        prompt = p._build_system_prompt()
        assert "Echo Agent" in prompt
        assert "Echo everything" in prompt

    def test_set_state(self) -> None:
        p = EchoPersona()
        p._set_state(2)
        assert p.ctx.state == 2

    def test_assign_directives_sets_states(self) -> None:
        nexus = self._make_nexus()
        p = EchoPersona()
        p.nexus = nexus
        p._assign_directives([EchoDirective])
        assert "EchoDirective" in p.states
        assert len(p.directives) == 1

    async def test_memory_disabled_skips_chronicle(self) -> None:
        nexus = self._make_nexus()
        p = EchoPersona(memory_enabled=False)
        p.nexus = nexus
        p._assign_directives([EchoDirective])
        s = Signal(content="no memory", cause_by="EchoDirective")
        p.put_signal(s)
        # Run observe; with memory disabled, nothing is recorded
        await p._observe()
        assert p.ctx.chronicle.count() == 0
