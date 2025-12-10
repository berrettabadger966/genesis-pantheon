"""CraftCode directive: generates Python source files."""

from __future__ import annotations

from typing import Any

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import CodingContext, DirectiveOutput

_CODE_PROMPT = """\
You are an expert Python engineer. Write complete, production-ready
Python code for the file: {filename}

## System Design Reference
{design}

## Task Description
{task}

## Existing Code (if any)
{existing_code}

Requirements:
- Write complete, runnable Python code
- Follow PEP 8 conventions
- Include proper docstrings for all classes and functions
- Handle errors gracefully
- Use type hints throughout
- Do NOT include TODO comments
- Include all necessary imports

Respond with ONLY the Python code inside a ```python ... ``` block.
"""


class CraftCode(Directive):
    """Generates Python source code for a single file.

    Takes a CodingContext (or string) as input and produces a
    complete Python file as a DirectiveOutput.
    """

    name: str = "CraftCode"
    desc: str = "Write Python implementation code"

    async def run(  # type: ignore[override]
        self,
        context: Any = None,
        **kwargs: object,
    ) -> DirectiveOutput:
        """Generate code for the file described in *context*.

        Args:
            context: CodingContext or requirement string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput containing the generated code.
        """
        if isinstance(context, CodingContext):
            filename = context.filename
            design = (
                context.design_doc.content
                if context.design_doc
                else "N/A"
            )
            task = (
                context.task_doc.content
                if context.task_doc
                else "Implement the described functionality."
            )
            existing = (
                context.code_doc.content
                if context.code_doc
                else ""
            )
        else:
            filename = "output.py"
            design = "N/A"
            task = str(context) if context else ""
            existing = ""

        prompt = _CODE_PROMPT.format(
            filename=filename,
            design=design,
            task=task,
            existing_code=existing or "None",
        )
        content = await self._ask(prompt)
        # Extract just the code block if present
        from genesis_pantheon.utils.common import CodeParser

        code = CodeParser.parse_code("python", content)
        return DirectiveOutput(content=code or content)


__all__ = ["CraftCode"]
