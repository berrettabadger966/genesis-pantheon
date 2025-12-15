"""Base Directive class for GenesisPantheon."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from genesis_pantheon.nexus_mixin import NexusMixin
from genesis_pantheon.schema import (
    CodingContext,
    DirectiveOutput,
    RunCodeContext,
    TestingContext,
)


class SerializationMixin(BaseModel):
    """Provides JSON serialization helpers."""

    def to_dict(self) -> dict:
        """Serialise to a plain dict.

        Returns:
            Model as a plain dictionary.
        """
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> SerializationMixin:
        """Restore from a plain dict.

        Args:
            data: Previously serialized dict.

        Returns:
            Reconstructed instance.
        """
        return cls(**data)


class Directive(SerializationMixin, NexusMixin, BaseModel):
    """Base class for all directives (actions) in GenesisPantheon.

    A Directive encapsulates a discrete task that a Persona can
    execute by calling ``run()``.  Sub-classes must override
    ``run()`` to implement their specific logic.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = ""
    input_context: CodingContext | TestingContext | RunCodeContext | str | None = ""
    prefix: str = ""
    desc: str = ""
    node: Any | None = Field(default=None, exclude=True)
    oracle_name_or_type: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _set_name_from_class(cls, values: Any) -> Any:
        """Automatically set ``name`` from the class name."""
        if isinstance(values, dict) and not values.get("name"):
            values["name"] = cls.__name__
        return values

    @model_validator(mode="after")
    def _configure_oracle(self) -> Directive:
        """Ensure the oracle is set up from Nexus when ready."""
        return self

    def set_prefix(self, prefix: str) -> Directive:
        """Set the system-prompt prefix for this directive.

        Args:
            prefix: Prefix string to prepend to the oracle's system
                prompt.

        Returns:
            Self (for chaining).
        """
        self.prefix = prefix
        if self._nexus is not None or self._private_nexus is not None:
            try:
                oracle = self.oracle
                oracle.system_prompt = prefix
            except Exception:
                pass
        return self

    async def _ask(
        self,
        prompt: str,
        system_msgs: list | None = None,
    ) -> str:
        """Invoke the oracle with the given prompt.

        Sets the oracle's system_prompt from ``self.prefix`` before
        calling ``ask()``.

        Args:
            prompt: User-facing prompt.
            system_msgs: Additional system context messages.

        Returns:
            Oracle response string.
        """
        o = self.oracle
        if self.prefix:
            o.system_prompt = self.prefix
        return await o.ask(
            prompt,
            system_msgs=system_msgs,
            stream=o.config.stream,
        )

    async def run(self, *args: Any, **kwargs: Any) -> DirectiveOutput:
        """Execute the directive.

        Sub-classes must override this method.

        Returns:
            DirectiveOutput with the result.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.run() is not implemented."
        )


__all__ = ["SerializationMixin", "Directive"]
