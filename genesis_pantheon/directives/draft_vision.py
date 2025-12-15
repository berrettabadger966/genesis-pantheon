"""DraftVision directive: generates a Product Requirements Document."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import DirectiveOutput

_PRD_PROMPT = """\
You are a Vision Director (product manager) creating a comprehensive
Product Requirements Document (PRD) for the following project:

{requirement}

Write a detailed PRD that includes:

## Original Requirements
State the original requirement.

## Product Goals
List 3 clear, measurable product goals.

## User Stories
List 5-7 user stories in "As a <user>, I want <feature>, so that
<benefit>" format.

## Competitive Analysis
Brief analysis of 3-5 competitors or similar products.

## Competitive Quadrant Chart
A mermaid quadrantChart showing competitor positioning.

## Requirement Analysis
Technical and business requirements analysis.

## Requirement Pool
List requirements as:
- P0 (must-have): Critical requirements
- P1 (should-have): Important requirements
- P2 (nice-to-have): Optional requirements

## UI Design Draft
High-level description of the user interface.

## Anything Unclear
Note any ambiguities or open questions.

Format the PRD clearly with all sections. Be specific and actionable.
"""


class DraftVision(Directive):
    """Generates a Product Requirements Document from a user directive.

    Subscribes to UserDirective signals and produces a structured PRD
    that downstream personas (SystemArchitect, etc.) can act on.
    """

    name: str = "DraftVision"
    desc: str = "Draft a Product Requirements Document (PRD)"

    async def run(  # type: ignore[override]
        self, context: str = "", **kwargs: object
    ) -> DirectiveOutput:
        """Generate a PRD for the given requirement context.

        Args:
            context: User requirement text.
            **kwargs: Ignored extra keyword arguments.

        Returns:
            DirectiveOutput containing the PRD markdown.
        """
        prompt = _PRD_PROMPT.format(requirement=context or "")
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


__all__ = ["DraftVision"]
