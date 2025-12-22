"""MissionCoordinator persona: project management agent."""

from __future__ import annotations

from genesis_pantheon.directives.allocate_tasks import AllocateTasks
from genesis_pantheon.directives.design_system import DesignSystem
from genesis_pantheon.personas.persona import Persona


class MissionCoordinator(Persona):
    """Mission Coordinator (project manager) persona.

    Subscribes to DesignSystem signals and breaks the system design
    into implementable coding tasks via AllocateTasks.
    """

    name: str = "Eve"
    profile: str = "Mission Coordinator"
    goal: str = (
        "Break down the system design into concrete, actionable "
        "tasks and ensure smooth execution by the engineering team"
    )
    constraints: str = (
        "Be specific in task descriptions; identify dependencies "
        "clearly; ensure no task is ambiguous"
    )

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._assign_directives([AllocateTasks])
        self._subscribe_to([DesignSystem])


__all__ = ["MissionCoordinator"]
