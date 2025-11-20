"""YAML-backed Pydantic base model."""

from pathlib import Path
from typing import Optional, Union

import yaml
from pydantic import BaseModel


class YamlModel(BaseModel):
    """BaseModel that can be serialised to / from YAML files."""

    @classmethod
    def read(cls, path: Union[str, Path]) -> "YamlModel":
        """Load model from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Instantiated model.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        data = cls.read_yaml(path)
        return cls(**data)

    def write(self, path: Union[str, Path]) -> None:
        """Serialise model to a YAML file.

        Args:
            path: Destination file path.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(str(dest), "w", encoding="utf-8") as fh:
            yaml.safe_dump(
                self.model_dump(mode="json"),
                fh,
                default_flow_style=False,
                allow_unicode=True,
            )

    @classmethod
    def read_yaml(
        cls,
        path: Union[str, Path],
        *,
        default: Optional[dict] = None,
    ) -> dict:
        """Read a YAML file and return the raw dict.

        Args:
            path: Path to the YAML file.
            default: Default dict if the file is empty or missing.

        Returns:
            Parsed YAML as a dictionary.
        """
        p = Path(path)
        if not p.exists():
            return default or {}
        with open(str(p), encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if data is None:
            return default or {}
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a YAML mapping at {path}, got {type(data)}"
            )
        return data


__all__ = ["YamlModel"]
