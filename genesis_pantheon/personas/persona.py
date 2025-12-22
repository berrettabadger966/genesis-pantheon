"""Base Persona (agent) class for GenesisPantheon."""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    model_validator,
)

from genesis_pantheon.chronicle import Chronicle
from genesis_pantheon.directives.base import Directive, SerializationMixin
from genesis_pantheon.logger import logger
from genesis_pantheon.nexus_mixin import NexusMixin
from genesis_pantheon.schema import Signal, SignalQueue
from genesis_pantheon.utils.common import any_to_str

if TYPE_CHECKING:
    pass


class PersonaReactMode(str, Enum):
    """Controls how a Persona decides its next directive."""

    REACT = "react"
    BY_ORDER = "by_order"
    PLAN_AND_ACT = "plan_and_act"


class PersonaContext(BaseModel):
    """Runtime context for a single Persona.

    Holds the signal buffer, message history, and current state
    for one agent instance.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    arena: Any | None = Field(default=None, exclude=True)
    signal_buffer: SignalQueue = Field(
        default_factory=SignalQueue, exclude=True
    )
    chronicle: Chronicle = Field(default_factory=Chronicle)
    working_memory: Chronicle = Field(default_factory=Chronicle)
    state: int = Field(default=-1)
    current_directive: Directive | None = Field(
        default=None, exclude=True
    )
    subscriptions: set[str] = Field(default_factory=set)
    news: list[Signal] = Field(default_factory=list, exclude=True)
    react_mode: PersonaReactMode = PersonaReactMode.REACT
    max_react_cycles: int = 1

    @property
    def relevant_signals(self) -> list[Signal]:
        """Signals in history that match this persona's subscriptions.

        Returns:
            Filtered list of Signal objects.
        """
        return self.chronicle.get_by_actions(self.subscriptions)

    @property
    def history(self) -> list[Signal]:
        """All signals stored in this persona's chronicle.

        Returns:
            Full signal history.
        """
        return self.chronicle.get()


class Persona(SerializationMixin, NexusMixin, BaseModel):
    """Base agent class for GenesisPantheon.

    A Persona is an autonomous agent that:
    - Subscribes to certain Signal types
    - Observes new signals arriving in its buffer
    - Thinks about which directive to execute next
    - Acts by running the directive and publishing the result
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str = ""
    profile: str = ""
    goal: str = ""
    constraints: str = ""
    description: str = ""
    is_human: bool = False
    memory_enabled: bool = True

    persona_id: str = ""
    states: list[str] = []
    directives: list[SerializeAsAny[Directive]] = Field(
        default_factory=list, validate_default=True
    )
    ctx: PersonaContext = Field(default_factory=PersonaContext)

    @model_validator(mode="after")
    def _configure_actions(self) -> Persona:
        """Propagate the Nexus context to all directives."""
        for directive in self.directives:
            directive.nexus = self.nexus
            if self.prefix:
                directive.set_prefix(self.prefix)
        return self

    @property
    def prefix(self) -> str:
        """System prompt prefix derived from profile, goal, constraints."""
        return self._build_system_prompt()

    def _assign_directives(
        self, directive_classes: list[Any]
    ) -> None:
        """Instantiate and register directive classes.

        Args:
            directive_classes: List of Directive subclasses (not
                instances) to assign to this persona.
        """
        self.directives = []
        for dc in directive_classes:
            instance = dc()
            instance.nexus = self.nexus
            instance.set_prefix(self.prefix)
            self.directives.append(instance)
        self.states = [d.name for d in self.directives]

    def _subscribe_to(self, directive_types: Iterable) -> None:
        """Subscribe to signals produced by the given directive types.

        Args:
            directive_types: Iterable of directive classes or strings.
        """
        self.ctx.subscriptions = {
            any_to_str(t) for t in directive_types
        }

    def _set_state(self, state: int) -> None:
        """Set the current state index.

        Args:
            state: Index into ``self.states``.
        """
        self.ctx.state = state

    def _set_current_directive(self, directive: Directive) -> None:
        """Update the currently executing directive.

        Args:
            directive: Directive that is about to run.
        """
        self.ctx.current_directive = directive

    async def _observe(self) -> int:
        """Collect new signals from the buffer matching subscriptions.

        Returns:
            Number of new signals observed.
        """
        pending = self.ctx.signal_buffer.pop_all()
        self.ctx.news = []  # always reset news before observing
        if not pending:
            return 0
        matching = [
            s
            for s in pending
            if (
                not self.ctx.subscriptions
                or s.cause_by in self.ctx.subscriptions
            )
        ]
        if self.memory_enabled:
            self.ctx.chronicle.add_batch(matching)
        self.ctx.news = matching
        logger.debug(
            f"[{self.name}] Observed {len(matching)} "
            f"matching signals (of {len(pending)} pending)"
        )
        return len(matching)

    async def _think(self) -> bool:
        """Choose the next directive to execute.

        In BY_ORDER mode advances through directives sequentially.
        In REACT mode selects based on incoming signal types.

        Returns:
            True when a directive was selected; False otherwise.
        """
        if not self.directives:
            return False

        if self.ctx.react_mode == PersonaReactMode.BY_ORDER:
            next_state = self.ctx.state + 1
            if next_state >= len(self.directives):
                return False
            self._set_state(next_state)
            self._set_current_directive(
                self.directives[next_state]
            )
            return True

        # REACT mode: pick based on subscriptions
        if not self.ctx.news:
            return False

        # Default to first directive
        self._set_state(0)
        self._set_current_directive(self.directives[0])
        return True

    async def _act(self) -> Signal:
        """Execute the current directive and return a result Signal.

        Returns:
            Signal encapsulating the directive output.

        Raises:
            NotImplementedError: Subclasses with custom logic should
                override this method.
        """
        if self.ctx.current_directive is None:
            return Signal(content="", sent_from=self.name)

        directive = self.ctx.current_directive
        # Pass the most recent signal's content as context
        context = (
            self.ctx.news[-1].content if self.ctx.news else ""
        )
        result = await directive.run(context=context)
        signal = Signal(
            content=result.content,
            structured_content=result.structured_content,
            sent_from=self.name,
            cause_by=directive.name,
        )
        if self.memory_enabled:
            signal_copy = signal.model_copy()
            signal_copy.role = "assistant"
            self.ctx.chronicle.add(signal_copy)
        return signal

    async def _react(self) -> Signal:
        """Execute directives in REACT mode until complete.

        Returns:
            Last produced Signal.
        """
        result = Signal(content="", sent_from=self.name)
        for _ in range(self.ctx.max_react_cycles):
            has_action = await self._think()
            if not has_action:
                break
            result = await self._act()
        return result

    async def _act_by_order(self) -> Signal:
        """Execute all directives sequentially in BY_ORDER mode.

        Returns:
            Last produced Signal.
        """
        result = Signal(content="", sent_from=self.name)
        self._set_state(-1)
        while True:
            has_action = await self._think()
            if not has_action:
                break
            result = await self._act()
        return result

    async def run(
        self, signal: Signal | None = None
    ) -> Signal | None:
        """Main execution entry point.

        Observes the signal buffer, then runs the appropriate
        reaction loop based on ``react_mode``.

        Args:
            signal: Optional signal to push directly into the buffer
                before observing.

        Returns:
            Result Signal or None if nothing was observed.
        """
        if signal is not None:
            self.put_signal(signal)

        n_observed = await self._observe()
        if n_observed == 0:
            return None

        mode = self.ctx.react_mode
        if mode == PersonaReactMode.BY_ORDER:
            return await self._act_by_order()
        return await self._react()

    def put_signal(self, signal: Signal) -> None:
        """Push a signal into this persona's receive buffer.

        Args:
            signal: Signal to enqueue.
        """
        self.ctx.signal_buffer.push(signal)

    @property
    def is_idle(self) -> bool:
        """True when the signal buffer is empty and no news pending.

        Returns:
            Idle state as a boolean.
        """
        return (
            self.ctx.signal_buffer.empty
            and not self.ctx.news
        )

    def _build_system_prompt(self) -> str:
        """Construct the system prompt string for this persona.

        Returns:
            System prompt incorporating profile, name, goal, and
            constraints.
        """
        return (
            f"You are a {self.profile}, named {self.name}. "
            f"Your goal is {self.goal}. "
            f"Constraints: {self.constraints}"
        )


__all__ = ["PersonaReactMode", "PersonaContext", "Persona"]
