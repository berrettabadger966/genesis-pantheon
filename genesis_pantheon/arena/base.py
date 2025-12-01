"""Arena: message broker and execution environment."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from genesis_pantheon.chronicle import Chronicle
from genesis_pantheon.constants import SIGNAL_ROUTE_TO_ALL
from genesis_pantheon.logger import logger
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.schema import Signal

if TYPE_CHECKING:
    from genesis_pantheon.personas.persona import Persona


class Arena(BaseModel):
    """Message broker and execution environment for Personas.

    The Arena routes Signals between Personas and drives the main
    execution loop by calling ``run()`` on each active persona.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    personas: dict[str, Any] = Field(default_factory=dict)
    chronicle: Chronicle = Field(default_factory=Chronicle)
    desc: str = ""
    context: Nexus = Field(default_factory=Nexus)

    def add_persona(self, persona: Persona) -> None:
        """Register a single persona in the arena.

        The persona's Nexus context is updated to the arena's shared
        context so all personas share the same configuration and budget.

        Args:
            persona: Persona instance to register.
        """
        persona.nexus = self.context
        # Propagate nexus to all directives
        for directive in persona.directives:
            directive.nexus = self.context
        self.personas[persona.name] = persona
        logger.debug(
            f"[Arena] Added persona: {persona.name} "
            f"({persona.profile})"
        )

    def add_personas(self, personas: list[Persona]) -> None:
        """Register multiple personas at once.

        Args:
            personas: List of Persona instances to register.
        """
        for p in personas:
            self.add_persona(p)

    def publish_signal(self, signal: Signal) -> bool:
        """Dispatch a signal to all relevant personas.

        Adds the signal to the arena chronicle and pushes it into
        the buffer of each persona that should receive it.

        Args:
            signal: Signal to publish.

        Returns:
            True if at least one persona received the signal.
        """
        self.chronicle.add(signal)
        recipients = 0
        for name, persona in self.personas.items():
            if (
                SIGNAL_ROUTE_TO_ALL in signal.send_to
                or name in signal.send_to
            ):
                persona.put_signal(signal)
                recipients += 1
                logger.debug(
                    f"[Arena] Delivered signal "
                    f"cause_by={signal.cause_by!r} "
                    f"to={name!r}"
                )
        return recipients > 0

    @property
    def is_idle(self) -> bool:
        """True when all personas have empty signal buffers.

        Returns:
            Boolean idle status.
        """
        return all(p.is_idle for p in self.personas.values())

    @property
    def history(self) -> list[Signal]:
        """All signals published to this arena.

        Returns:
            Chronological list of Signal objects.
        """
        return self.chronicle.get()

    async def run(self) -> list[Signal]:
        """Execute one round: run each non-idle persona.

        Each persona that has pending signals is run concurrently.
        Resulting signals are published back into the arena for
        other personas to consume.

        Returns:
            List of new signals produced this round.
        """
        active = [
            p
            for p in self.personas.values()
            if not p.is_idle
        ]
        if not active:
            logger.debug("[Arena] No active personas this round.")
            return []

        logger.info(
            f"[Arena] Running {len(active)} active persona(s): "
            f"{[p.name for p in active]}"
        )

        tasks = [p.run() for p in active]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        new_signals: list[Signal] = []
        for persona, result in zip(active, results):
            if isinstance(result, Exception):
                logger.exception(
                    f"[Arena] Persona {persona.name} raised: {result}"
                )
                continue
            if result is not None and isinstance(result, Signal):
                if result.content:
                    new_signals.append(result)
                    self.publish_signal(result)

        logger.info(
            f"[Arena] Round complete. "
            f"New signals: {len(new_signals)}"
        )
        return new_signals

    def archive(self, auto: bool = True) -> None:
        """Archive the arena state (placeholder for persistence).

        Args:
            auto: When True the archive operation is performed
                automatically; when False it is a no-op.
        """
        if auto:
            logger.debug(
                f"[Arena] Archiving {self.chronicle.count()} signals."
            )


__all__ = ["Arena"]
