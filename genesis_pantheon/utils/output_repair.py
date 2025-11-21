"""Utilities for repairing malformed LLM output."""

import json
import re


def extract_state_value_from_output(
    output: str, state_count: int
) -> int:
    """Extract a numeric state index from LLM output.

    Searches for the first integer in *output* that falls within
    ``[0, state_count - 1]``.

    Args:
        output: Raw LLM response string.
        state_count: Total number of valid states.

    Returns:
        Parsed state index, or -1 if none found.
    """
    numbers = re.findall(r"\b(\d+)\b", output)
    for num_str in numbers:
        idx = int(num_str)
        if 0 <= idx < state_count:
            return idx
    return -1


def repair_llm_json_output(output: str) -> str:
    """Attempt to repair common JSON formatting errors in LLM output.

    Handles:
    - Stripping markdown code fences
    - Removing trailing commas before ``}`` or ``]``
    - Replacing single quotes with double quotes (basic cases)

    Args:
        output: Potentially malformed JSON string.

    Returns:
        Best-effort repaired JSON string.
    """
    # Strip markdown fences
    stripped = re.sub(
        r"^```(?:json)?\s*\n?(.*?)\n?```$",
        r"\1",
        output.strip(),
        flags=re.DOTALL,
    )
    # Remove trailing commas before closing braces/brackets
    no_trailing = re.sub(
        r",\s*([}\]])",
        r"\1",
        stripped,
    )
    # Validate; if broken try replacing single-quote keys/values
    try:
        json.loads(no_trailing)
        return no_trailing
    except json.JSONDecodeError:
        pass
    # Replace single-quoted strings with double quotes (simple cases)
    single_to_double = re.sub(
        r"(?<![\\])'((?:[^'\\]|\\.)*)'",
        r'"\1"',
        no_trailing,
    )
    try:
        json.loads(single_to_double)
        return single_to_double
    except json.JSONDecodeError:
        pass
    # Return best attempt
    return no_trailing


__all__ = [
    "extract_state_value_from_output",
    "repair_llm_json_output",
]
