"""Oracle registry and factory for GenesisPantheon."""

from __future__ import annotations

from genesis_pantheon.configs.oracle_config import (
    OracleApiType,
    OracleConfig,
)
from genesis_pantheon.oracles.base import BaseOracle

ORACLE_REGISTRY: dict[str, type[BaseOracle]] = {}


def register_oracle(api_type: OracleApiType):
    """Class decorator that registers an oracle implementation.

    Usage::

        @register_oracle(OracleApiType.OPENAI)
        class OpenAIOracle(BaseOracle):
            ...

    Args:
        api_type: The OracleApiType this class handles.

    Returns:
        Decorator function.
    """

    def decorator(cls: type[BaseOracle]) -> type[BaseOracle]:
        ORACLE_REGISTRY[api_type.value] = cls
        return cls

    return decorator


def create_oracle_instance(config: OracleConfig) -> BaseOracle:
    """Instantiate the correct oracle for the given config.

    Args:
        config: OracleConfig describing which provider to use.

    Returns:
        Configured BaseOracle instance.

    Raises:
        ValueError: If no oracle is registered for the api_type.
    """
    key = (
        config.api_type.value
        if hasattr(config.api_type, "value")
        else str(config.api_type)
    )
    if key not in ORACLE_REGISTRY:
        available = ", ".join(ORACLE_REGISTRY.keys())
        raise ValueError(
            f"No oracle registered for api_type={key!r}. "
            f"Available: {available}"
        )
    oracle_cls = ORACLE_REGISTRY[key]
    return oracle_cls(config=config)


__all__ = [
    "ORACLE_REGISTRY",
    "register_oracle",
    "create_oracle_instance",
]
