"""InsightHunter persona: research and analysis agent."""

from __future__ import annotations

from typing import Any

from genesis_pantheon.directives.base import Directive
from genesis_pantheon.directives.user_directive import UserDirective
from genesis_pantheon.logger import logger
from genesis_pantheon.personas.persona import Persona
from genesis_pantheon.schema import DirectiveOutput


class ResearchDirective(Directive):
    """Conducts web research and summarises findings."""

    name: str = "ResearchDirective"
    desc: str = "Research a topic and produce a structured report"

    async def run(  # type: ignore[override]
        self, context: Any = None, **kwargs: Any
    ) -> DirectiveOutput:
        """Research the topic described in *context*.

        Args:
            context: Research query or requirement string.
            **kwargs: Ignored.

        Returns:
            DirectiveOutput with the research report.
        """
        query = str(context) if context else "general research"
        prompt = (
            f"You are a research expert. Conduct thorough research "
            f"on the following topic and produce a well-structured "
            f"report:\n\n{query}\n\n"
            "Include:\n"
            "1. Executive Summary\n"
            "2. Key Findings\n"
            "3. Detailed Analysis\n"
            "4. Data and Evidence\n"
            "5. Conclusions and Recommendations\n\n"
            "Cite sources where applicable. Be accurate and objective."
        )
        content = await self._ask(prompt)
        return DirectiveOutput(content=content)


class InsightHunter(Persona):
    """Insight Hunter (researcher) persona.

    Subscribes to UserDirective signals and conducts research,
    producing structured reports for downstream personas.
    """

    name: str = "Frank"
    profile: str = "Insight Hunter"
    goal: str = (
        "Gather comprehensive, accurate information and transform it "
        "into actionable insights through rigorous research"
    )
    constraints: str = (
        "Rely only on verified information; clearly distinguish "
        "facts from analysis; cite sources where possible"
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._assign_directives([ResearchDirective])
        self._subscribe_to([UserDirective])
        logger.debug(f"[{self.name}] InsightHunter initialised")


__all__ = ["InsightHunter"]
