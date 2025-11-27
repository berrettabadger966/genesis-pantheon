"""Oracle (LLM provider) adapters for GenesisPantheon."""

# Import oracle implementations to trigger registration
from genesis_pantheon.oracles import (  # noqa: F401
    anthropic_oracle,
    azure_oracle,
    gemini_oracle,
    human_oracle,
    ollama_oracle,
    openai_oracle,
)
from genesis_pantheon.oracles.base import BaseOracle
from genesis_pantheon.oracles.registry import (
    ORACLE_REGISTRY,
    create_oracle_instance,
    register_oracle,
)

__all__ = [
    "BaseOracle",
    "ORACLE_REGISTRY",
    "register_oracle",
    "create_oracle_instance",
]
