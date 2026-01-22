"""Tests for serialization utility functions."""

from __future__ import annotations

import json

import pytest

from genesis_pantheon.utils.serialization import (
    directive_output_mapping_to_str,
    directive_output_schema_to_mapping,
    directive_output_str_to_mapping,
)


class TestDirectiveOutputSchemaToMapping:
    def test_simple_string_field(self) -> None:
        schema = {
            "properties": {
                "title": {"type": "string"},
            }
        }
        mapping = directive_output_schema_to_mapping(schema)
        assert mapping == {"title": "string"}

    def test_integer_field(self) -> None:
        schema = {
            "properties": {
                "score": {"type": "integer"},
            }
        }
        mapping = directive_output_schema_to_mapping(schema)
        assert mapping == {"score": "integer"}

    def test_multiple_fields(self) -> None:
        schema = {
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"},
            }
        }
        mapping = directive_output_schema_to_mapping(schema)
        assert len(mapping) == 3
        assert mapping["name"] == "string"
        assert mapping["age"] == "integer"

    def test_any_of_field_uses_first_type(self) -> None:
        schema = {
            "properties": {
                "value": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ]
                }
            }
        }
        mapping = directive_output_schema_to_mapping(schema)
        assert mapping["value"] == "string"

    def test_empty_schema_returns_empty_mapping(self) -> None:
        schema: dict = {}
        mapping = directive_output_schema_to_mapping(schema)
        assert mapping == {}

    def test_empty_properties_returns_empty_mapping(self) -> None:
        schema = {"properties": {}}
        mapping = directive_output_schema_to_mapping(schema)
        assert mapping == {}

    def test_field_without_type_defaults_to_string(self) -> None:
        schema = {
            "properties": {
                "mystery": {"description": "no type here"},
            }
        }
        mapping = directive_output_schema_to_mapping(schema)
        assert mapping["mystery"] == "string"


class TestDirectiveOutputMappingToStr:
    def test_serializes_to_json_string(self) -> None:
        mapping = {"title": "string", "score": "integer"}
        result = directive_output_mapping_to_str(mapping)
        parsed = json.loads(result)
        assert parsed == mapping

    def test_empty_mapping(self) -> None:
        result = directive_output_mapping_to_str({})
        assert result == "{}"

    def test_preserves_non_ascii(self) -> None:
        mapping = {"título": "string"}
        result = directive_output_mapping_to_str(mapping)
        assert "título" in result


class TestDirectiveOutputStrToMapping:
    def test_deserializes_from_json_string(self) -> None:
        mapping_str = '{"title": "string", "score": "integer"}'
        result = directive_output_str_to_mapping(mapping_str)
        assert result == {"title": "string", "score": "integer"}

    def test_empty_object(self) -> None:
        result = directive_output_str_to_mapping("{}")
        assert result == {}

    def test_round_trip(self) -> None:
        original = {"field_a": "string", "field_b": "boolean"}
        encoded = directive_output_mapping_to_str(original)
        decoded = directive_output_str_to_mapping(encoded)
        assert decoded == original

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            directive_output_str_to_mapping("not json")
