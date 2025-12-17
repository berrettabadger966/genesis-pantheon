"""SystemArchitect persona: software architecture agent."""

from __future__ import annotations

from genesis_pantheon.directives.design_system import DesignSystem
from genesis_pantheon.directives.draft_vision import DraftVision
from genesis_pantheon.personas.persona import Persona


class SystemArchitect(Persona):
    """System Architect persona.

    Subscribes to DraftVision (PRD) signals and produces a system
    design document via DesignSystem.
    """

    name: str = "Bob"
    profile: str = "System Architect"
    goal: str = (
        "Design a clean, scalable, and maintainable system "
        "architecture based on product requirements"
    )
    constraints: str = (
        "Follow SOLID principles; prefer simplicity over complexity; "
        "design for testability and extensibility"
    )

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._assign_directives([DesignSystem])
        self._subscribe_to([DraftVision])


__all__ = ["SystemArchitect"]
