"""Tests for genesis_pantheon.utils.common module."""

from __future__ import annotations

from pathlib import Path

import pytest

from genesis_pantheon.utils.common import (
    CodeParser,
    any_to_name,
    any_to_str,
    any_to_str_set,
    aread,
    awrite,
    read_json_file,
    write_json_file,
)


class TestAnyToStr:
    def test_string_passthrough(self) -> None:
        assert any_to_str("hello") == "hello"

    def test_class_name(self) -> None:
        class MyClass:
            pass

        assert any_to_str(MyClass) == "MyClass"

    def test_instance_class_name(self) -> None:
        class MyClass:
            pass

        assert any_to_str(MyClass()) == "MyClass"

    def test_integer(self) -> None:
        assert any_to_str(42) == "42"

    def test_none(self) -> None:
        assert any_to_str(None) == "None"


class TestAnyToStrSet:
    def test_single_string(self) -> None:
        result = any_to_str_set("hello")
        assert result == {"hello"}

    def test_list_of_strings(self) -> None:
        result = any_to_str_set(["a", "b", "c"])
        assert result == {"a", "b", "c"}

    def test_none_returns_empty(self) -> None:
        result = any_to_str_set(None)
        assert result == set()

    def test_class_in_iterable(self) -> None:
        class Foo:
            pass

        result = any_to_str_set([Foo, "bar"])
        assert "Foo" in result
        assert "bar" in result


class TestAnyToName:
    def test_string_passthrough(self) -> None:
        assert any_to_name("hello") == "hello"

    def test_class_returns_name(self) -> None:
        class MyClass:
            pass

        assert any_to_name(MyClass) == "MyClass"

    def test_instance_returns_class_name(self) -> None:
        class MyClass:
            pass

        assert any_to_name(MyClass()) == "MyClass"


class TestCodeParser:
    def test_parse_code_block(self) -> None:
        text = "Here is code:\n```python\nprint('hello')\n```"
        result = CodeParser.parse_code("python", text)
        assert "print('hello')" in result

    def test_parse_code_any_block(self) -> None:
        text = "```\nx = 1\n```"
        result = CodeParser.parse_code("", text)
        assert "x = 1" in result

    def test_parse_code_no_block(self) -> None:
        text = "just plain text"
        result = CodeParser.parse_code("python", text)
        assert result == "just plain text"

    def test_parse_blocks_multiple(self) -> None:
        text = "# Section A\nContent A\n# Section B\nContent B"
        blocks = CodeParser.parse_blocks(text)
        assert "Section A" in blocks
        assert "Section B" in blocks

    def test_parse_str(self) -> None:
        text = "Model: gpt-4-turbo"
        result = CodeParser.parse_str("Model", text)
        assert result == "gpt-4-turbo"

    def test_parse_file_list(self) -> None:
        text = "# Files\n- main.py\n- utils.py\n- game.py"
        result = CodeParser.parse_file_list("Files", text)
        assert "main.py" in result
        assert "utils.py" in result

    def test_parse_block_section(self) -> None:
        text = (
            "## Product Goals\nBuild a great product\n"
            "## User Stories\nAs a user..."
        )
        result = CodeParser.parse_block("Product Goals", text)
        assert "great product" in result


async def test_aread_and_awrite(tmp_path: Path) -> None:
    target = tmp_path / "test_file.txt"
    await awrite(target, "Hello, GenesisPantheon!")
    content = await aread(target)
    assert content == "Hello, GenesisPantheon!"


async def test_awrite_creates_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "dir" / "file.txt"
    await awrite(target, "nested content")
    assert target.exists()
    content = await aread(target)
    assert content == "nested content"


def test_read_write_json_file(tmp_path: Path) -> None:
    data = {"key": "value", "number": 42}
    dest = tmp_path / "test.json"
    write_json_file(dest, data)
    loaded = read_json_file(dest)
    assert loaded["key"] == "value"
    assert loaded["number"] == 42


def test_read_json_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_json_file(tmp_path / "nonexistent.json")
