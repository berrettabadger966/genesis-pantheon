"""Tests for LLM output repair utilities."""

from __future__ import annotations

from genesis_pantheon.utils.output_repair import (
    extract_state_value_from_output,
    repair_llm_json_output,
)


class TestExtractStateValueFromOutput:
    def test_extracts_valid_state(self) -> None:
        result = extract_state_value_from_output("State: 2", 5)
        assert result == 2

    def test_returns_minus_one_when_no_number(self) -> None:
        result = extract_state_value_from_output("no number here", 5)
        assert result == -1

    def test_returns_minus_one_when_out_of_range(self) -> None:
        result = extract_state_value_from_output("10", 5)
        assert result == -1

    def test_extracts_first_valid_number(self) -> None:
        result = extract_state_value_from_output("choose 1 from 99", 5)
        assert result == 1

    def test_state_zero_is_valid(self) -> None:
        result = extract_state_value_from_output("0", 3)
        assert result == 0

    def test_with_mixed_text(self) -> None:
        result = extract_state_value_from_output(
            "I think option 3 is best.", 5
        )
        assert result == 3

    def test_empty_output(self) -> None:
        result = extract_state_value_from_output("", 5)
        assert result == -1

    def test_state_count_one_allows_only_zero(self) -> None:
        result = extract_state_value_from_output("0", 1)
        assert result == 0
        result2 = extract_state_value_from_output("1", 1)
        assert result2 == -1


class TestRepairLlmJsonOutput:
    def test_valid_json_returned_unchanged(self) -> None:
        good = '{"key": "value"}'
        result = repair_llm_json_output(good)
        import json

        assert json.loads(result) == {"key": "value"}

    def test_strips_markdown_code_fence(self) -> None:
        fenced = '```json\n{"key": "value"}\n```'
        result = repair_llm_json_output(fenced)
        import json

        assert json.loads(result) == {"key": "value"}

    def test_strips_generic_code_fence(self) -> None:
        fenced = '```\n{"x": 1}\n```'
        result = repair_llm_json_output(fenced)
        import json

        assert json.loads(result) == {"x": 1}

    def test_removes_trailing_commas_in_object(self) -> None:
        bad = '{"a": 1, "b": 2,}'
        result = repair_llm_json_output(bad)
        import json

        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": 2}

    def test_removes_trailing_commas_in_array(self) -> None:
        bad = '[1, 2, 3,]'
        result = repair_llm_json_output(bad)
        import json

        assert json.loads(result) == [1, 2, 3]

    def test_returns_best_effort_for_unfixable(self) -> None:
        broken = "this is not json at all"
        result = repair_llm_json_output(broken)
        assert isinstance(result, str)

    def test_empty_string_returns_empty(self) -> None:
        result = repair_llm_json_output("")
        assert isinstance(result, str)

    def test_nested_json_preserved(self) -> None:
        nested = '{"outer": {"inner": [1, 2, 3]}}'
        result = repair_llm_json_output(nested)
        import json

        parsed = json.loads(result)
        assert parsed["outer"]["inner"] == [1, 2, 3]
