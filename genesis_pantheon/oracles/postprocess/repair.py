"""Output repair utilities for LLM responses."""

from __future__ import annotations

import json
import re


def extract_state_from_output(output: str, state_count: int) -> int:
    """Extract a numeric state index from LLM output.

    Scans for the first integer in *output* that is a valid state
    index ``[0, state_count - 1]``.

    Args:
        output: Raw LLM response string.
        state_count: Total number of valid states.

    Returns:
        Valid state index, or -1 if none found.
    """
    for match in re.finditer(r"\b(\d+)\b", output):
        idx = int(match.group(1))
        if 0 <= idx < state_count:
            return idx
    return -1


def repair_json_output(output: str) -> str:
    """Best-effort repair of malformed JSON from an LLM.

    Steps applied:
    1. Strip markdown code fences.
    2. Remove trailing commas before ``}`` or ``]``.
    3. Attempt single-quote to double-quote conversion.

    Args:
        output: Potentially malformed JSON string.

    Returns:
        Repaired JSON string (may still be invalid if too broken).
    """
    # Strip code fences
    cleaned = re.sub(
        r"^```(?:json)?\s*\n?(.*?)\n?```$",
        r"\1",
        output.strip(),
        flags=re.DOTALL,
    )
    # Remove trailing commas
    no_trailing = re.sub(r",\s*([}\]])", r"\1", cleaned)
    try:
        json.loads(no_trailing)
        return no_trailing
    except json.JSONDecodeError:
        pass
    # Replace simple single-quoted strings
    converted = re.sub(
        r"(?<![\\])'((?:[^'\\]|\\.)*)'",
        r'"\1"',
        no_trailing,
    )
    try:
        json.loads(converted)
        return converted
    except json.JSONDecodeError:
        pass
    return no_trailing


def extract_markdown_block(
    output: str, block_type: str = "python"
) -> str:
    """Extract a fenced code block from markdown output.

    Args:
        output: Markdown string potentially containing code blocks.
        block_type: Language tag to match (e.g. ``python``).

    Returns:
        Code content, or empty string if not found.
    """
    pattern = rf"```{re.escape(block_type)}\s*\n(.*?)```"
    match = re.search(pattern, output, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: try any code fence
    generic = re.search(r"```(?:\w+)?\s*\n(.*?)```", output, re.DOTALL)
    if generic:
        return generic.group(1).strip()
    return ""


__all__ = [
    "extract_state_from_output",
    "repair_json_output",
    "extract_markdown_block",
]
