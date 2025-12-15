"""DesignSystem directive: generates system architecture design."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import DirectiveOutput

_DESIGN_PROMPT = """\
You are a System Architect. Based on the following Product Requirements
Document (PRD), design a complete, scalable system architecture.

PRD:
{prd}

Create a System Design Document that includes:

## Implementation Approach
Explain how you will implement the system, key technical decisions,
and the overall approach.

## File List
List ALL Python files that need to be created. Be specific and
include every file needed (e.g. main.py, game.py, ui.py, etc.)

## Data Structures and Interfaces
Define the main classes, their attributes, and their relationships
using a mermaid classDiagram.

## Program Flow
Describe the main execution flow using a mermaid sequenceDiagram.

## Anything Unclear
Note any ambiguities or open questions.

Be concrete, pragmatic, and production-ready in your design.
"""


class DesignSystem(Directive):
    """Produces a system design document from a PRD signal.

    Subscribes to DraftVision signals and outputs a technical
    architecture document for the CodeCrafter and MissionCoordinator.
    """

    name: str = "DesignSystem"
    desc: str = "Design the system architecture from a PRD"

    async def run(  # type: ignore[override]
        self, context: str = "", **kwargs: object
    ) -> DirectiveOutput:
        """Generate a system design from PRD content.

        Args:
            context: PRD content string.
            **kwargs: Ignored extra keyword arguments.

        Returns:
            DirectiveOutput containing the design document.
        """
        prompt = _DESIGN_PROMPT.format(prd=context or "")
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


__all__ = ["DesignSystem"]
