"""CondenseCode directive: summarises multiple code files."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import CodeCondenseContext, DirectiveOutput

_CONDENSE_PROMPT = """\
You are a senior engineer creating a concise summary of a codebase.

## System Design
{design}

## Tasks
{tasks}

## Code Files
{code_files}

Write a structured summary that:
1. Describes the overall architecture and how files relate
2. Lists key classes and their responsibilities
3. Identifies the main entry points and data flow
4. Notes important patterns or conventions used
5. Highlights any technical debt or areas for improvement

Keep the summary concise but comprehensive enough to give a new
engineer a complete mental model of the codebase.
"""


class CondenseCode(Directive):
    """Produces a concise summary of a multi-file codebase."""

    name: str = "CondenseCode"
    desc: str = "Summarise a codebase into a concise overview"

    async def run(  # type: ignore[override]
        self, context: object = None, **kwargs: object
    ) -> DirectiveOutput:
        """Summarise the codebase described in *context*.

        Args:
            context: CodeCondenseContext or description string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput with the condensed summary.
        """
        if isinstance(context, CodeCondenseContext):
            design = context.design_filename
            tasks = context.task_filename
            code_files = ", ".join(context.codes_filenames)
        else:
            design = ""
            tasks = ""
            code_files = str(context) if context else ""

        prompt = _CONDENSE_PROMPT.format(
            design=design or "N/A",
            tasks=tasks or "N/A",
            code_files=code_files or "N/A",
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


__all__ = ["CondenseCode"]
