"""AllocateTasks directive: breaks design into coding tasks."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import DirectiveOutput

_ALLOCATE_PROMPT = """\
You are a Project Manager breaking down a system design into concrete
implementation tasks.

## System Design
{design}

Create a detailed task allocation document with:

## Required Python Packages
List all third-party Python packages needed (name and version).

## Logic Analysis
For each file in the File List, describe:
- The file's purpose
- Key classes and functions to implement
- Dependencies on other files

## Task List
Number each task clearly. For each task:
- File to implement
- Specific functions/classes to write
- Dependencies that must be complete first

## Shared Knowledge
Document any shared utilities, constants, or patterns that engineers
should know about.

## Anything Unclear
Note any ambiguities in the design that need clarification.

Be specific and comprehensive. Each task should be clear enough for
an engineer to implement without additional context.
"""


class AllocateTasks(Directive):
    """Converts a system design into implementable coding tasks."""

    name: str = "AllocateTasks"
    desc: str = "Break system design into coding tasks"

    async def run(  # type: ignore[override]
        self, context: object = None, **kwargs: object
    ) -> DirectiveOutput:
        """Generate task allocations from *context*.

        Args:
            context: System design content string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput with task allocation document.
        """
        design = str(context) if context else ""
        prompt = _ALLOCATE_PROMPT.format(design=design)
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


__all__ = ["AllocateTasks"]
