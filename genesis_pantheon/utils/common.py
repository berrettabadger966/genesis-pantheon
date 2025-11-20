"""Common utility functions for GenesisPantheon."""

import functools
import importlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Union

import aiofiles

from genesis_pantheon.logger import logger
from genesis_pantheon.utils.exceptions import BudgetExceededError


def any_to_str(val: Any) -> str:
    """Convert any value to its canonical string representation.

    For strings the value is returned as-is. For classes the
    ``__name__`` is used. For instances the class name is used.

    Args:
        val: Value to convert.

    Returns:
        String representation.
    """
    primitive_types = (
        int, float, bool, bytes, list, dict, set, tuple, type(None)
    )
    if isinstance(val, str):
        return val
    if isinstance(val, type):
        return val.__name__
    if callable(val) and hasattr(val, "__name__"):
        return val.__name__
    if isinstance(val, primitive_types):
        return str(val)
    return type(val).__name__


def any_to_str_set(val: Any) -> set:
    """Convert an iterable (or single value) to a set of strings.

    Args:
        val: Single value or iterable of values.

    Returns:
        Set of string representations.
    """
    if val is None:
        return set()
    if isinstance(val, (str, type)):
        return {any_to_str(val)}
    try:
        return {any_to_str(v) for v in val}
    except TypeError:
        return {any_to_str(val)}


def any_to_name(val: Any) -> str:
    """Get the display name of a class or instance.

    Args:
        val: Class, instance, or string.

    Returns:
        Human-readable name.
    """
    if isinstance(val, str):
        return val
    if isinstance(val, type):
        return val.__name__
    return type(val).__name__


class CodeParser:
    """Utilities for parsing code blocks and structured text."""

    @classmethod
    def parse_block(cls, block: str, text: str) -> str:
        """Extract content from a named markdown section.

        Args:
            block: Section heading to find.
            text: Full text to search.

        Returns:
            Content under the section heading.
        """
        pattern = (
            rf"#{{1,6}}\s*{re.escape(block)}\s*\n"
            rf"(.*?)(?=\n#{{1,6}}|\Z)"
        )
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    @classmethod
    def parse_blocks(cls, text: str) -> dict:
        """Extract all markdown sections as a dict.

        Args:
            text: Markdown text with sections.

        Returns:
            Mapping of section name to section content.
        """
        pattern = r"#{1,6}\s*(.+?)\s*\n(.*?)(?=\n#{1,6}|\Z)"
        matches = re.findall(pattern, text, re.DOTALL)
        return {
            heading.strip(): body.strip() for heading, body in matches
        }

    @classmethod
    def parse_code(cls, block: str = "", text: str = "") -> str:
        """Extract code from a fenced code block.

        Args:
            block: Language tag (e.g. ``python``). Empty matches any.
            text: Text containing the fenced code block.

        Returns:
            Code content without the fence markers.
        """
        if block:
            pattern = rf"```{re.escape(block)}\s*\n(.*?)```"
        else:
            pattern = r"```(?:\w+)?\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If no fenced block, return text as-is
        return text.strip()

    @classmethod
    def parse_str(cls, block: str = "", text: str = "") -> str:
        """Extract a string value from a labelled line.

        Args:
            block: Label to search for.
            text: Text to search within.

        Returns:
            Value following the label on the same line.
        """
        pattern = rf"{re.escape(block)}\s*[:\-]\s*(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip().strip("\"'")
        return ""

    @classmethod
    def parse_file_list(cls, block: str = "", text: str = "") -> list:
        """Extract a list of file names from a section.

        Args:
            block: Section name to search inside.
            text: Full text to search.

        Returns:
            List of file name strings.
        """
        section = cls.parse_block(block, text) if block else text
        # Match lines that look like file paths
        items = re.findall(
            r"[`'\"]?([\w/\\.+-]+\.\w+)[`'\"]?", section
        )
        return [i.strip() for i in items if i]


def serialize_decorator(func: Callable) -> Callable:
    """Auto-save collective state before and restore after execution.

    This decorator wraps an async method on a ``Collective`` instance
    and logs start/stop events for observability.

    Args:
        func: Async function to wrap.

    Returns:
        Wrapped async function.
    """

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        logger.info(
            f"[{self.__class__.__name__}] Starting: {func.__name__}"
        )
        try:
            result = await func(self, *args, **kwargs)
            logger.info(
                f"[{self.__class__.__name__}] Completed: {func.__name__}"
            )
            return result
        except BudgetExceededError:
            logger.warning(
                f"[{self.__class__.__name__}] Budget exceeded during "
                f"{func.__name__}"
            )
            raise
        except Exception as exc:
            logger.exception(
                f"[{self.__class__.__name__}] Error in {func.__name__}: "
                f"{exc}"
            )
            raise

    return wrapper


def role_raise_decorator(func: Callable) -> Callable:
    """Wrap a persona async method to log and re-raise exceptions.

    Args:
        func: Async method to wrap.

    Returns:
        Wrapped async method.
    """

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(self, *args, **kwargs)
        except Exception as exc:
            logger.exception(
                f"[{getattr(self, 'name', self.__class__.__name__)}] "
                f"Error in {func.__name__}: {exc}"
            )
            raise

    return wrapper


async def aread(
    filename: Union[str, Path], encoding: str = "utf-8"
) -> str:
    """Asynchronously read a text file.

    Args:
        filename: Path to the file.
        encoding: File encoding.

    Returns:
        File contents as a string.
    """
    async with aiofiles.open(str(filename), encoding=encoding) as fh:
        return await fh.read()


async def awrite(
    filename: Union[str, Path],
    data: str,
    encoding: str = "utf-8",
) -> None:
    """Asynchronously write text to a file, creating parent dirs.

    Args:
        filename: Destination file path.
        data: Content to write.
        encoding: File encoding.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(str(path), "w", encoding=encoding) as fh:
        await fh.write(data)


def read_json_file(file_path: Union[str, Path]) -> dict:
    """Read a JSON file and return its contents as a dict.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(str(file_path), encoding="utf-8") as fh:
        return json.load(fh)


def write_json_file(
    file_path: Union[str, Path], data: dict
) -> None:
    """Write a dict to a JSON file with pretty-printing.

    Args:
        file_path: Destination path.
        data: Dictionary to serialise.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def import_class(class_name: str, module_path: str) -> type:
    """Dynamically import a class from a module path.

    Args:
        class_name: Name of the class to import.
        module_path: Dotted module path (e.g.
            ``genesis_pantheon.personas.persona``).

    Returns:
        The imported class object.

    Raises:
        ImportError: If the module cannot be imported.
        AttributeError: If the class does not exist in the module.
    """
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


__all__ = [
    "any_to_str",
    "any_to_str_set",
    "any_to_name",
    "CodeParser",
    "serialize_decorator",
    "role_raise_decorator",
    "aread",
    "awrite",
    "read_json_file",
    "write_json_file",
    "import_class",
]
