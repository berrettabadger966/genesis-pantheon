"""VisionDirector persona: product management agent."""

from __future__ import annotations

from genesis_pantheon.directives.draft_vision import DraftVision
from genesis_pantheon.directives.review_design import ReviewDesign
from genesis_pantheon.directives.user_directive import UserDirective
from genesis_pantheon.personas.persona import Persona


class VisionDirector(Persona):
    """Vision Director (product manager) persona.

    Subscribes to UserDirective signals and produces a PRD via
    DraftVision. Also performs design review via ReviewDesign.
    """

    name: str = "Alice"
    profile: str = "Vision Director"
    goal: str = (
        "Efficiently create a successful product that meets user "
        "needs and business goals"
    )
    constraints: str = (
        "Prioritize user needs and market demands; make clear "
        "data-driven decisions; recommend an appropriate tech stack"
    )

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._assign_directives([DraftVision, ReviewDesign])
        self._subscribe_to([UserDirective])


__all__ = ["VisionDirector"]
