"""DiagnoseError directive: analyses errors and suggests fixes."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import DirectiveOutput

_DIAGNOSE_PROMPT = """\
You are an expert Python debugger. Analyse the following error and
provide a diagnosis and fix.

## Error Output
{error}

## Code
```python
{code}
```

## Task Description
{task}

Provide:

## Error Diagnosis
Explain what caused the error in plain language.

## Root Cause
Identify the specific root cause.

## Fix
Describe what changes are needed.

## Fixed Code
Provide the complete corrected code inside a ```python ... ``` block.

Be precise and ensure the fix fully resolves the error.
"""


class DiagnoseError(Directive):
    """Analyses error output and suggests code fixes."""

    name: str = "DiagnoseError"
    desc: str = "Diagnose and fix code errors"

    async def run(  # type: ignore[override]
        self, context: object = None, **kwargs: object
    ) -> DirectiveOutput:
        """Diagnose the error described in *context*.

        Args:
            context: RunCodeContext, RunCodeResult, or error string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput with diagnosis and fixed code.
        """
        from genesis_pantheon.schema import RunCodeContext, RunCodeResult

        if isinstance(context, RunCodeResult):
            error = context.stdout
            code = ""
            task = context.summary
        elif isinstance(context, RunCodeContext):
            error = context.output or ""
            code = context.code or ""
            task = ""
        else:
            error = str(context) if context else ""
            code = ""
            task = ""

        prompt = _DIAGNOSE_PROMPT.format(
            error=error, code=code, task=task
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


__all__ = ["DiagnoseError"]
