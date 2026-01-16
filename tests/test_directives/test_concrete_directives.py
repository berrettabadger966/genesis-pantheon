"""Tests for concrete directive implementations."""

from __future__ import annotations

from genesis_pantheon.directives.add_requirement import AddRequirement
from genesis_pantheon.directives.allocate_tasks import AllocateTasks
from genesis_pantheon.directives.condense_code import CondenseCode
from genesis_pantheon.directives.craft_code import CraftCode
from genesis_pantheon.directives.design_system import DesignSystem
from genesis_pantheon.directives.diagnose_error import DiagnoseError
from genesis_pantheon.directives.draft_vision import DraftVision
from genesis_pantheon.directives.generate_tests import GenerateTests
from genesis_pantheon.directives.review_code import ReviewCode
from genesis_pantheon.directives.review_design import ReviewDesign
from genesis_pantheon.directives.user_directive import UserDirective
from genesis_pantheon.nexus import Nexus
from genesis_pantheon.schema import CodingContext, Document
from tests.conftest import MockOracle


def _nexus(responses=None) -> Nexus:
    nexus = Nexus()
    nexus._oracle = MockOracle(
        responses=responses or ["directive response"]
    )
    return nexus


class TestUserDirective:
    def test_name_is_user_directive(self) -> None:
        d = UserDirective()
        assert d.name == "UserDirective"

    async def test_run_returns_signal(self) -> None:
        d = UserDirective()
        d.nexus = _nexus()
        result = await d.run(requirement="Build a calc")
        assert result.content == "Build a calc"


class TestAddRequirement:
    def test_instantiation(self) -> None:
        d = AddRequirement()
        assert d.name == "AddRequirement"


class TestDraftVision:
    def test_name(self) -> None:
        d = DraftVision()
        assert d.name == "DraftVision"

    async def test_run_returns_directive_output(self) -> None:
        d = DraftVision()
        d.nexus = _nexus(
            responses=["## Goals\nBuild great product\n"]
        )
        output = await d.run(requirement="Build a calculator")
        assert output.content

    async def test_run_with_empty_requirement(self) -> None:
        d = DraftVision()
        d.nexus = _nexus(responses=["some prd"])
        output = await d.run(requirement="")
        assert isinstance(output.content, str)


class TestDesignSystem:
    def test_name(self) -> None:
        d = DesignSystem()
        assert d.name == "DesignSystem"

    async def test_run_returns_directive_output(self) -> None:
        d = DesignSystem()
        d.nexus = _nexus(responses=["System design here"])
        output = await d.run(requirement="Based on PRD...")
        assert output.content


class TestReviewDesign:
    def test_name(self) -> None:
        d = ReviewDesign()
        assert d.name == "ReviewDesign"

    async def test_run_produces_review(self) -> None:
        d = ReviewDesign()
        d.nexus = _nexus(responses=["LGTM - design looks good"])
        output = await d.run(requirement="design content here")
        assert output.content


class TestCraftCode:
    def test_name(self) -> None:
        d = CraftCode()
        assert d.name == "CraftCode"

    async def test_run_with_string_context(self) -> None:
        d = CraftCode()
        d.nexus = _nexus(
            responses=["```python\nprint('hello')\n```"]
        )
        output = await d.run(context="implement main.py")
        assert output.content

    async def test_run_with_coding_context(self) -> None:
        d = CraftCode()
        d.nexus = _nexus(responses=["```python\nx = 1\n```"])
        doc = Document(filename="design.md", content="design here")
        coding_ctx = CodingContext(
            filename="main.py", design_doc=doc
        )
        output = await d.run(context=coding_ctx)
        assert output.content


class TestReviewCode:
    def test_name(self) -> None:
        d = ReviewCode()
        assert d.name == "ReviewCode"

    async def test_run_returns_review(self) -> None:
        d = ReviewCode()
        d.nexus = _nexus(responses=["LGTM, no issues found"])
        output = await d.run(context="code to review")
        assert output.content


class TestGenerateTests:
    def test_name(self) -> None:
        d = GenerateTests()
        assert d.name == "GenerateTests"

    async def test_run_returns_test_code(self) -> None:
        d = GenerateTests()
        d.nexus = _nexus(
            responses=["```python\ndef test_something(): pass\n```"]
        )
        output = await d.run(context="code to test")
        assert output.content


class TestAllocateTasks:
    def test_name(self) -> None:
        d = AllocateTasks()
        assert d.name == "AllocateTasks"

    async def test_run_returns_task_list(self) -> None:
        d = AllocateTasks()
        d.nexus = _nexus(
            responses=["Task 1: main.py\nTask 2: utils.py"]
        )
        output = await d.run(requirement="based on design...")
        assert output.content


class TestCondenseCode:
    def test_name(self) -> None:
        d = CondenseCode()
        assert d.name == "CondenseCode"

    async def test_run_returns_summary(self) -> None:
        d = CondenseCode()
        d.nexus = _nexus(responses=["Code implements XYZ..."])
        output = await d.run(context="code content here")
        assert output.content


class TestDiagnoseError:
    def test_name(self) -> None:
        d = DiagnoseError()
        assert d.name == "DiagnoseError"

    async def test_run_returns_diagnosis(self) -> None:
        d = DiagnoseError()
        d.nexus = _nexus(
            responses=["The error is on line 5: NameError"]
        )
        output = await d.run(context="error trace here")
        assert output.content
