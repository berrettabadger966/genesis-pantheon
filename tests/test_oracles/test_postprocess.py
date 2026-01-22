"""Tests for oracle postprocessing utilities."""

from __future__ import annotations

import json

from genesis_pantheon.oracles.postprocess.repair import (
    extract_markdown_block,
    extract_state_from_output,
    repair_json_output,
)


class TestExtractStateFromOutput:
    def test_finds_valid_state(self) -> None:
        assert extract_state_from_output("choose 2", 5) == 2

    def test_returns_minus_one_when_no_match(self) -> None:
        assert extract_state_from_output("no numbers", 5) == -1

    def test_returns_minus_one_when_out_of_range(self) -> None:
        assert extract_state_from_output("9", 5) == -1

    def test_zero_is_valid(self) -> None:
        assert extract_state_from_output("0", 3) == 0

    def test_first_valid_number_wins(self) -> None:
        # "7" is out of range for 5, "2" is valid
        assert extract_state_from_output("7 then 2", 5) == 2

    def test_empty_string(self) -> None:
        assert extract_state_from_output("", 5) == -1


class TestRepairJsonOutput:
    def test_valid_json_unchanged(self) -> None:
        data = '{"a": 1}'
        result = repair_json_output(data)
        assert json.loads(result) == {"a": 1}

    def test_strips_json_code_fence(self) -> None:
        fenced = '```json\n{"key": "val"}\n```'
        result = repair_json_output(fenced)
        assert json.loads(result) == {"key": "val"}

    def test_strips_generic_fence(self) -> None:
        fenced = '```\n{"x": 1}\n```'
        result = repair_json_output(fenced)
        assert json.loads(result) == {"x": 1}

    def test_removes_trailing_comma_object(self) -> None:
        bad = '{"a": 1,}'
        result = repair_json_output(bad)
        assert json.loads(result) == {"a": 1}

    def test_removes_trailing_comma_array(self) -> None:
        bad = '[1, 2,]'
        result = repair_json_output(bad)
        assert json.loads(result) == [1, 2]

    def test_unfixable_returns_string(self) -> None:
        result = repair_json_output("completely broken{{")
        assert isinstance(result, str)


class TestExtractMarkdownBlock:
    def test_extracts_python_block(self) -> None:
        text = "Here is the code:\n```python\nprint('hi')\n```\nEnd."
        result = extract_markdown_block(text, "python")
        assert result == "print('hi')"

    def test_extracts_generic_block_as_fallback(self) -> None:
        text = "```\nx = 1\n```"
        result = extract_markdown_block(text, "python")
        assert result == "x = 1"

    def test_returns_empty_when_no_block(self) -> None:
        result = extract_markdown_block("no code here", "python")
        assert result == ""

    def test_extracts_multiline_block(self) -> None:
        text = "```python\ndef foo():\n    return 42\n```"
        result = extract_markdown_block(text, "python")
        assert "def foo" in result
        assert "return 42" in result

    def test_extracts_json_block(self) -> None:
        text = '```json\n{"key": "value"}\n```'
        result = extract_markdown_block(text, "json")
        assert result == '{"key": "value"}'

    def test_block_type_is_optional(self) -> None:
        text = "```python\nresult = True\n```"
        result = extract_markdown_block(text)  # default: "python"
        assert "result = True" in result
