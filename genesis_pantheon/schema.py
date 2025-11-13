"""Core data models for GenesisPantheon."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_serializer,
    field_validator,
)

from genesis_pantheon.constants import SIGNAL_ROUTE_TO_ALL
from genesis_pantheon.utils.common import aread

# ---------------------------------------------------------------------------
# SignalQueue
# ---------------------------------------------------------------------------


class SignalQueue(BaseModel):
    """Async-safe queue for signals between personas."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    _queue: asyncio.Queue = PrivateAttr(
        default_factory=asyncio.Queue
    )

    def push(self, signal: Signal) -> None:
        """Synchronously enqueue a signal.

        Args:
            signal: Signal to enqueue.
        """
        self._queue.put_nowait(signal)

    async def put(self, signal: Signal) -> None:
        """Asynchronously enqueue a signal.

        Args:
            signal: Signal to enqueue.
        """
        await self._queue.put(signal)

    async def get(self) -> Signal:
        """Asynchronously dequeue the next signal.

        Returns:
            Next Signal from the queue.
        """
        return await self._queue.get()

    def pop_all(self) -> list[Signal]:
        """Drain the queue and return all pending signals.

        Returns:
            List of all queued signals.
        """
        results: list[Signal] = []
        while not self._queue.empty():
            try:
                results.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return results

    @property
    def empty(self) -> bool:
        """True when no signals are queued."""
        return self._queue.empty()


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------


class Signal(BaseModel):
    """Core communication unit between personas.

    Signals flow through the Arena and are dispatched to Personas
    that subscribe to the directive type that produced them.
    """

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex
    )
    content: str
    structured_content: BaseModel | None = None
    role: str = "user"
    cause_by: str = Field(default="", validate_default=True)
    sent_from: str = Field(default="", validate_default=True)
    send_to: set = Field(
        default_factory=lambda: {SIGNAL_ROUTE_TO_ALL},
        validate_default=True,
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("cause_by", mode="before")
    @classmethod
    def _default_cause_by(cls, v: Any) -> str:
        """Auto-set cause_by to UserDirective when empty."""
        if not v:
            return "UserDirective"
        if isinstance(v, str):
            return v
        if hasattr(v, "__name__"):
            return v.__name__
        if hasattr(v, "__class__"):
            return v.__class__.__name__
        return str(v)

    @field_validator("sent_from", mode="before")
    @classmethod
    def _normalise_sent_from(cls, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        if hasattr(v, "name"):
            return v.name
        return str(v)

    @field_validator("send_to", mode="before")
    @classmethod
    def _normalise_send_to(cls, v: Any) -> set:
        if v is None:
            return {SIGNAL_ROUTE_TO_ALL}
        if isinstance(v, str):
            return {v}
        if isinstance(v, (list, set, tuple)):
            return {
                item if isinstance(item, str) else str(item)
                for item in v
            }
        return {str(v)}

    @field_serializer("send_to")
    def _ser_send_to(self, v: set) -> list:
        return sorted(v)

    @field_serializer("structured_content")
    def _ser_structured(self, v: BaseModel | None) -> Any:
        if v is None:
            return None
        return v.model_dump()

    def is_for(self, persona_name: str) -> bool:
        """Return True if this signal should be delivered to persona.

        Args:
            persona_name: Name of the candidate recipient persona.

        Returns:
            True if the signal is addressed to ``persona_name`` or to
            all personas.
        """
        return (
            SIGNAL_ROUTE_TO_ALL in self.send_to
            or persona_name in self.send_to
        )


# ---------------------------------------------------------------------------
# DirectiveOutput
# ---------------------------------------------------------------------------


class DirectiveOutput(BaseModel):
    """Result produced by a Directive after execution."""

    content: str
    structured_content: BaseModel | None = None

    def to_signal(
        self,
        sent_from: str = "",
        send_to: set | None = None,
        cause_by: str = "",
    ) -> Signal:
        """Convert this output into a Signal for publishing.

        Args:
            sent_from: Name of the originating persona.
            send_to: Target personas (default: all).
            cause_by: Directive class name that produced this output.

        Returns:
            Signal ready for publishing to the Arena.
        """
        return Signal(
            content=self.content,
            structured_content=self.structured_content,
            sent_from=sent_from,
            send_to=send_to or {SIGNAL_ROUTE_TO_ALL},
            cause_by=cause_by,
        )


# ---------------------------------------------------------------------------
# Document / Documents
# ---------------------------------------------------------------------------


class Document(BaseModel):
    """A text document stored in the project repository."""

    root_path: str = ""
    filename: str = ""
    content: str = ""

    @property
    def root_relative_path(self) -> str:
        """Path relative to the repository root.

        Returns:
            String path joining root and filename.
        """
        if self.root_path and self.filename:
            return str(Path(self.root_path) / self.filename)
        return self.filename or self.root_path

    @classmethod
    async def load(
        cls,
        filename: str | Path,
        project_path: str | Path | None = None,
    ) -> Document | None:
        """Asynchronously load a Document from the filesystem.

        Args:
            filename: Name or relative path of the file.
            project_path: Root directory to resolve relative paths.

        Returns:
            Document instance, or None if the file does not exist.
        """
        if project_path:
            full = Path(project_path) / filename
        else:
            full = Path(filename)
        if not full.exists():
            return None
        content = await aread(full)
        return cls(
            root_path=str(full.parent),
            filename=str(Path(filename).name),
            content=content,
        )


class Documents(BaseModel):
    """A collection of Document objects keyed by filename."""

    docs: dict[str, Document] = Field(default_factory=dict)

    @classmethod
    def from_iterable(cls, documents: Any) -> Documents:
        """Build a Documents collection from an iterable.

        Args:
            documents: Iterable of Document instances.

        Returns:
            Documents collection.
        """
        return cls(
            docs={doc.filename: doc for doc in documents}
        )


# ---------------------------------------------------------------------------
# Coding / execution context models
# ---------------------------------------------------------------------------


class CodingContext(BaseModel):
    """Context passed to code-generation directives."""

    filename: str
    design_doc: Document | None = None
    task_doc: Document | None = None
    code_doc: Document | None = None


class TestingContext(BaseModel):
    """Context passed to test-generation directives."""

    filename: str
    code_doc: Document
    test_doc: Document | None = None


class RunCodeContext(BaseModel):
    """Context describing how to execute code."""

    mode: str = "script"
    code: str | None = None
    code_filename: str = ""
    test_code: str | None = None
    test_filename: str = ""
    command: list[str] = Field(default_factory=list)
    working_directory: str = ""
    additional_python_paths: list[str] = Field(
        default_factory=list
    )
    output: str | None = None


class RunCodeResult(BaseModel):
    """Result from executing code via ExecuteCode directive."""

    summary: str
    stdout: str
    returncode: int

    @property
    def success(self) -> bool:
        """True when the process exited with code 0."""
        return self.returncode == 0


class CodeCondenseContext(BaseModel):
    """Context for summarising multiple code files."""

    codes_filenames: list[str] = Field(default_factory=list)
    design_filename: str = ""
    task_filename: str = ""


__all__ = [
    "SignalQueue",
    "Signal",
    "DirectiveOutput",
    "Document",
    "Documents",
    "CodingContext",
    "TestingContext",
    "RunCodeContext",
    "RunCodeResult",
    "CodeCondenseContext",
]
