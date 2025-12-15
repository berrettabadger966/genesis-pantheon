"""ReviewDesign directive: reviews and refines a system design."""

from __future__ import annotations

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.schema import DirectiveOutput

_REVIEW_PROMPT = """\
You are a senior Vision Director reviewing a system design document.

System Design:
{design}

Review the design and provide:

## Review Result
LGTM (if acceptable) or LGTM with comments (if minor changes needed)
or Reject (if major redesign needed).

## Review Comment
Specific, actionable feedback on:
1. Architecture decisions
2. Completeness of the file list
3. Data structure design
4. Security considerations
5. Scalability concerns

If the design is sound, write "LGTM" and briefly summarise the
strengths. If improvements are needed, list specific changes.

Be constructive and concise.
"""


class ReviewDesign(Directive):
    """Reviews a system design document and provides feedback.

    Produces a review signal that the SystemArchitect or CodeCrafter
    can act upon.
    """

    name: str = "ReviewDesign"
    desc: str = "Review and refine the system design document"

    async def run(  # type: ignore[override]
        self, context: str = "", **kwargs: object
    ) -> DirectiveOutput:
        """Review the given design document.

        Args:
            context: System design content to review.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput with the review.
        """
        prompt = _REVIEW_PROMPT.format(design=context or "")
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


__all__ = ["ReviewDesign"]
