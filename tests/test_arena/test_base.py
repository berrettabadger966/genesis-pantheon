"""Tests for the Arena environment."""

from __future__ import annotations

from genesis_pantheon.arena.base import Arena
from genesis_pantheon.directives.base import Directive, DirectiveOutput
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.personas.persona import Persona
from genesis_pantheon.schema import Signal
from tests.conftest import MockOracle


class PassthroughDirective(Directive):
    """Directive that returns a fixed response."""

    name: str = "PassthroughDirective"

    async def run(self, *args, **kwargs) -> DirectiveOutput:
        return DirectiveOutput(content="passthrough done")


class PassthroughPersona(Persona):
    name: str = "PassBot"
    profile: str = "Passthrough"
    goal: str = "Pass signals"
    constraints: str = ""


def _make_arena_with_nexus() -> Arena:
    nexus = Nexus()
    nexus._oracle = MockOracle(responses=["ok"])
    return Arena(context=nexus)


class TestArena:
    def test_initially_no_personas(self) -> None:
        arena = _make_arena_with_nexus()
        assert len(arena.personas) == 0

    def test_add_persona_registers_by_name(self) -> None:
        arena = _make_arena_with_nexus()
        p = PassthroughPersona()
        arena.add_persona(p)
        assert "PassBot" in arena.personas

    def test_add_personas_registers_all(self) -> None:
        arena = _make_arena_with_nexus()
        p1 = PassthroughPersona(name="Bot1")
        p2 = PassthroughPersona(name="Bot2")
        arena.add_personas([p1, p2])
        assert "Bot1" in arena.personas
        assert "Bot2" in arena.personas

    def test_add_persona_shares_nexus(self) -> None:
        arena = _make_arena_with_nexus()
        p = PassthroughPersona()
        arena.add_persona(p)
        # Persona's nexus should now reference the arena's context
        assert arena.personas["PassBot"].nexus is arena.context

    def test_publish_signal_to_all_delivers_to_everyone(self) -> None:
        arena = _make_arena_with_nexus()
        p1 = PassthroughPersona(name="A")
        p2 = PassthroughPersona(name="B")
        arena.add_personas([p1, p2])

        sig = Signal(content="broadcast")
        arena.publish_signal(sig)

        items_a = arena.personas["A"].ctx.signal_buffer.pop_all()
        items_b = arena.personas["B"].ctx.signal_buffer.pop_all()
        assert len(items_a) == 1
        assert len(items_b) == 1

    def test_publish_signal_to_specific_persona(self) -> None:
        arena = _make_arena_with_nexus()
        p1 = PassthroughPersona(name="Target")
        p2 = PassthroughPersona(name="Bystander")
        arena.add_personas([p1, p2])

        sig = Signal(content="targeted", send_to={"Target"})
        arena.publish_signal(sig)

        target_items = arena.personas["Target"].ctx.signal_buffer.pop_all()
        bystander_items = (
            arena.personas["Bystander"].ctx.signal_buffer.pop_all()
        )
        assert len(target_items) == 1
        assert len(bystander_items) == 0

    def test_publish_signal_adds_to_chronicle(self) -> None:
        arena = _make_arena_with_nexus()
        sig = Signal(content="record me")
        arena.publish_signal(sig)
        assert arena.chronicle.count() == 1

    def test_publish_signal_returns_true_when_delivered(self) -> None:
        arena = _make_arena_with_nexus()
        p = PassthroughPersona()
        arena.add_persona(p)
        result = arena.publish_signal(Signal(content="hello"))
        assert result is True

    def test_publish_signal_returns_false_with_no_personas(self) -> None:
        arena = _make_arena_with_nexus()
        result = arena.publish_signal(Signal(content="nobody home"))
        assert result is False

    def test_is_idle_with_no_personas(self) -> None:
        arena = _make_arena_with_nexus()
        assert arena.is_idle is True

    def test_is_idle_with_all_idle_personas(self) -> None:
        arena = _make_arena_with_nexus()
        p = PassthroughPersona()
        arena.add_persona(p)
        assert arena.is_idle is True

    def test_is_not_idle_when_persona_has_signals(self) -> None:
        arena = _make_arena_with_nexus()
        p = PassthroughPersona()
        arena.add_persona(p)
        arena.publish_signal(Signal(content="pending"))
        assert arena.is_idle is False

    def test_history_reflects_chronicle(self) -> None:
        arena = _make_arena_with_nexus()
        arena.publish_signal(Signal(content="a"))
        arena.publish_signal(Signal(content="b"))
        assert len(arena.history) == 2

    async def test_run_calls_all_active_personas(self) -> None:
        nexus = Nexus()
        nexus._oracle = MockOracle(responses=["done"])
        arena = Arena(context=nexus)

        p = PassthroughPersona()
        nexus2 = Nexus()
        nexus2._oracle = MockOracle(responses=["done"])
        p.nexus = nexus2
        p._assign_directives([PassthroughDirective])
        # Subscribe to UserDirective so the persona consumes the trigger
        # without re-triggering itself from its own output
        p._subscribe_to(["UserDirective"])
        arena.add_persona(p)

        # Publish a UserDirective signal
        sig = Signal(content="run me", cause_by="UserDirective")
        arena.publish_signal(sig)
        assert not arena.is_idle

        new_signals = await arena.run()
        # PassBot should have run and produced one signal
        assert len(new_signals) >= 1

    def test_archive_does_not_raise(self, tmp_path) -> None:
        arena = _make_arena_with_nexus()
        # archive with auto=False should not raise
        arena.archive(auto=False)
