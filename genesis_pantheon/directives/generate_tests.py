"""GenerateTests directive: writes unit tests for Python files."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import DirectiveOutput, TestingContext

_TEST_PROMPT = """\
You are a Python testing expert. Write comprehensive pytest unit tests
for the following code.

## Code Under Test
File: {filename}

```python
{code}
```

Write tests that:
- Cover all public functions and classes
- Include happy-path and edge-case tests
- Use pytest fixtures where appropriate
- Mock external dependencies with pytest-mock
- Are clear and well-documented

Include all necessary imports. Use descriptive test function names
following the pattern ``test_<function>_<scenario>``.

Respond with ONLY the test code inside a ```python ... ``` block.
"""


class GenerateTests(Directive):
    """Generates pytest unit tests for a given code file."""

    name: str = "GenerateTests"
    desc: str = "Generate pytest unit tests for Python code"

    async def run(  # type: ignore[override]
        self, context: object = None, **kwargs: object
    ) -> DirectiveOutput:
        """Generate tests for the code described in *context*.

        Args:
            context: TestingContext or code string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput containing the test file content.
        """
        if isinstance(context, TestingContext):
            filename = context.filename
            code = context.code_doc.content
        else:
            filename = "code.py"
            code = str(context) if context else ""

        prompt = _TEST_PROMPT.format(filename=filename, code=code)
        content = await self._ask(prompt)
        from genesis_pantheon.utils.common import CodeParser

        tests = CodeParser.parse_code("python", content)
        return DirectiveOutput(content=tests or content)


__all__ = ["GenerateTests"]
