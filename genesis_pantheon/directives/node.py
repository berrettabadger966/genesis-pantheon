"""DirectiveNode: Structured I/O schema for directives."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, create_model

from genesis_pantheon.logger import logger
from genesis_pantheon.utils.output_repair import repair_llm_json_output


class DirectiveNode(BaseModel):
    """Defines the input/output schema for a single directive field.

    Nodes can be nested to build rich structured outputs.
    """

    key: str
    expected_type: type = str
    instruction: str
    example: str | dict | list = ""
    schema_type: str = "json"  # "json", "markdown", or "raw"
    children: list[DirectiveNode] = Field(default_factory=list)
    _filled_value: Any = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def value(self) -> Any:
        """The value populated by :meth:`fill`."""
        return self._filled_value

    def get(self, key: str) -> DirectiveNode | None:
        """Find a child node by key (recursive).

        Args:
            key: Key to search for.

        Returns:
            Matching DirectiveNode or None.
        """
        if self.key == key:
            return self
        for child in self.children:
            found = child.get(key)
            if found is not None:
                return found
        return None

    @classmethod
    def from_children(
        cls,
        key: str,
        nodes: list[DirectiveNode],
    ) -> DirectiveNode:
        """Create a parent node wrapping a list of child nodes.

        Args:
            key: Parent key name.
            nodes: Child DirectiveNode objects.

        Returns:
            Parent DirectiveNode.
        """
        return cls(
            key=key,
            expected_type=dict,
            instruction="Composite node",
            children=nodes,
        )

    def compile(
        self,
        req: str,
        schema_type: str,
        mode: str = "auto",
    ) -> str:
        """Build a prompt string for this node.

        Args:
            req: User requirement / context string.
            schema_type: Output format: ``json``, ``markdown``,
                or ``raw``.
            mode: Unused; reserved for future use.

        Returns:
            Prompt string for the oracle.
        """
        if self.children:
            fields_desc = "\n".join(
                f"  - {c.key}: {c.instruction}" for c in self.children
            )
            if schema_type == "json":
                example_keys = {
                    c.key: c.example or f"<{c.key}>" for c in self.children
                }
                example_str = json.dumps(example_keys, indent=2)
                return (
                    f"{req}\n\n"
                    f"Respond with a JSON object containing:\n"
                    f"{fields_desc}\n\n"
                    f"Example format:\n```json\n{example_str}\n```"
                )
            return (
                f"{req}\n\nProvide the following:\n{fields_desc}"
            )
        example_str = (
            json.dumps(self.example)
            if isinstance(self.example, (dict, list))
            else str(self.example)
        )
        if schema_type == "json":
            return (
                f"{req}\n\n"
                f"Task: {self.instruction}\n"
                f"Respond with a JSON object: "
                f'{{"{self.key}": <value>}}\n'
                f"Example: {{\"{ self.key}\": {example_str}}}"
            )
        return f"{req}\n\nTask: {self.instruction}"

    async def fill(
        self,
        req: str,
        oracle: Any,
        schema_type: str | None = None,
        mode: str = "auto",
    ) -> DirectiveNode:
        """Call the oracle to fill this node with a value.

        Args:
            req: Context / requirement string.
            oracle: BaseOracle instance to call.
            schema_type: Override the node's default schema type.
            mode: Prompt construction mode.

        Returns:
            Self with ``_filled_value`` set.
        """
        stype = schema_type or self.schema_type
        prompt = self.compile(req, stype, mode)
        raw = await oracle.ask(prompt, stream=False)
        self._filled_value = self._parse_response(raw, stype)
        logger.debug(
            f"[DirectiveNode] key={self.key} "
            f"filled={str(self._filled_value)[:80]}"
        )
        return self

    def _parse_response(self, raw: str, schema_type: str) -> Any:
        """Parse the oracle response according to schema_type.

        Args:
            raw: Raw oracle response text.
            schema_type: Expected format.

        Returns:
            Parsed value.
        """
        if schema_type == "raw":
            return raw
        if schema_type == "json":
            repaired = repair_llm_json_output(raw)
            try:
                data = json.loads(repaired)
                if isinstance(data, dict):
                    if self.key in data:
                        return data[self.key]
                    # If children, return the whole dict
                    if self.children:
                        return data
                return data
            except json.JSONDecodeError:
                return raw
        # markdown or fallback
        return raw

    def instruct_content(self) -> BaseModel | None:
        """Return the filled value as a Pydantic model if possible.

        Returns:
            BaseModel instance or None.
        """
        if not self.children or not isinstance(
            self._filled_value, dict
        ):
            return None
        mapping = {
            c.key: (type(self._filled_value.get(c.key, "")), ...)
            for c in self.children
        }
        try:
            model_cls = self.create_model_class(
                f"{self.key}Model", mapping
            )
            return model_cls(**self._filled_value)
        except Exception:
            return None

    @classmethod
    def create_model_class(
        cls,
        class_name: str,
        mapping: dict[str, Any],
    ) -> type[BaseModel]:
        """Dynamically create a Pydantic model class.

        Args:
            class_name: Name for the new model class.
            mapping: Field definitions as ``{name: (type, default)}``.

        Returns:
            A new BaseModel subclass.
        """
        # Normalise mapping to Pydantic field tuples
        fields: dict[str, Any] = {}
        for field_name, field_def in mapping.items():
            if isinstance(field_def, tuple):
                fields[field_name] = field_def
            else:
                fields[field_name] = (str, "")
        return create_model(class_name, **fields)


DirectiveNode.model_rebuild()

__all__ = ["DirectiveNode"]
