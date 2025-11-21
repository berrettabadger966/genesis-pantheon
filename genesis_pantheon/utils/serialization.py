"""Serialization helpers for directive outputs."""

import json


def directive_output_schema_to_mapping(schema: dict) -> dict:
    """Convert a Pydantic JSON schema to a flat key-type mapping.

    Args:
        schema: Pydantic model's ``model_json_schema()`` output.

    Returns:
        Dict mapping field names to their type strings.
    """
    properties = schema.get("properties", {})
    mapping: dict = {}
    for field_name, field_schema in properties.items():
        type_str = field_schema.get("type", "string")
        if "anyOf" in field_schema:
            types = [
                t.get("type", "string")
                for t in field_schema["anyOf"]
                if "type" in t
            ]
            type_str = types[0] if types else "string"
        mapping[field_name] = type_str
    return mapping


def directive_output_mapping_to_str(mapping: dict) -> str:
    """Serialise a field mapping to a JSON string.

    Args:
        mapping: Dict mapping field names to type strings.

    Returns:
        Compact JSON string representation.
    """
    return json.dumps(mapping, ensure_ascii=False)


def directive_output_str_to_mapping(mapping_str: str) -> dict:
    """Deserialise a JSON string back to a field mapping.

    Args:
        mapping_str: JSON string produced by
            :func:`directive_output_mapping_to_str`.

    Returns:
        Reconstructed mapping dict.

    Raises:
        json.JSONDecodeError: If the string is not valid JSON.
    """
    return json.loads(mapping_str)


__all__ = [
    "directive_output_schema_to_mapping",
    "directive_output_mapping_to_str",
    "directive_output_str_to_mapping",
]
