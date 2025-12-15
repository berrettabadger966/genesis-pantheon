"""ReviewCode directive: reviews generated code for quality."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import DirectiveOutput

_REVIEW_PROMPT = """\
You are a senior Python engineer performing a code review.

## Code to Review
File: {filename}

```python
{code}
```

## Task Description
{task}

Perform a thorough code review covering:
1. Correctness - does the code correctly implement the requirements?
2. Code style - PEP 8 compliance, naming conventions
3. Error handling - are exceptions handled appropriately?
4. Type hints - are types annotated correctly?
5. Security - are there any security concerns?
6. Performance - any obvious performance issues?
7. Testability - is the code easy to test?

Provide:
## Review Result
LGTM (no changes needed) or Changes Required

## Review Comments
Specific line-by-line feedback.

## Revised Code (if changes needed)
If changes are required, provide the complete revised file inside
a ```python ... ``` block.

Be constructive and specific.
"""


class ReviewCode(Directive):
    """Reviews generated code and optionally produces corrected code."""

    name: str = "ReviewCode"
    desc: str = "Review Python code for quality and correctness"

    async def run(  # type: ignore[override]
        self, context: object = None, **kwargs: object
    ) -> DirectiveOutput:
        """Review code described in *context*.

        Args:
            context: CodingContext or code string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput with review and optionally corrected code.
        """
        from genesis_pantheon.schema import CodingContext

        if isinstance(context, CodingContext):
            filename = context.filename
            code = (
                context.code_doc.content
                if context.code_doc
                else ""
            )
            task = (
                context.task_doc.content
                if context.task_doc
                else ""
            )
        else:
            filename = "code.py"
            code = str(context) if context else ""
            task = ""

        prompt = _REVIEW_PROMPT.format(
            filename=filename, code=code, task=task
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


__all__ = ["ReviewCode"]
