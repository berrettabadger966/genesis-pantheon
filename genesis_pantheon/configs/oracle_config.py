"""Oracle (LLM provider) configuration models."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class OracleApiType(str, Enum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    HUMAN = "human"


class OracleConfig(BaseModel):
    """Configuration for a single LLM provider (oracle).

    All sensitive values (api_key) should be set via environment
    variables or the blueprint.yaml config file — never hardcoded.
    """

    api_type: OracleApiType = OracleApiType.OPENAI
    model: str = "gpt-4-turbo"
    base_url: str = ""
    api_key: str = ""
    api_version: str = ""
    proxy: str = ""
    timeout: int = 300
    max_retries: int = 3
    pricing_plan: str = ""
    calc_usage: bool = True
    temperature: float = 0.0
    max_tokens: int = 4096
    stream: bool = True
    # Optional extra model kwargs forwarded to the provider
    extra_kwargs: dict = Field(default_factory=dict)

    @field_validator("temperature")
    @classmethod
    def _clamp_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError(
                f"temperature must be between 0.0 and 2.0, got {v}"
            )
        return v

    @field_validator("max_tokens")
    @classmethod
    def _positive_max_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(f"max_tokens must be positive, got {v}")
        return v

    @classmethod
    def default_openai(cls) -> "OracleConfig":
        """Return default OpenAI configuration."""
        return cls(api_type=OracleApiType.OPENAI, model="gpt-4-turbo")

    @classmethod
    def default_anthropic(cls) -> "OracleConfig":
        """Return default Anthropic configuration."""
        return cls(
            api_type=OracleApiType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
        )

    @classmethod
    def default_gemini(cls) -> "OracleConfig":
        """Return default Google Gemini configuration."""
        return cls(
            api_type=OracleApiType.GEMINI,
            model="gemini-1.5-pro",
        )

    @classmethod
    def for_ollama(
        cls, model: str = "llama3", base_url: str = "http://localhost:11434"
    ) -> "OracleConfig":
        """Return Ollama configuration."""
        return cls(
            api_type=OracleApiType.OLLAMA,
            model=model,
            base_url=base_url,
            api_key="ollama",
        )

    def is_valid(self) -> bool:
        """Check whether the config has the minimum required fields."""
        if self.api_type == OracleApiType.OLLAMA:
            return bool(self.base_url and self.model)
        if self.api_type == OracleApiType.HUMAN:
            return True
        return bool(self.api_key and self.model)

    class Config:
        use_enum_values = False

    # Pricing map (USD per 1k tokens) for common models
    _PRICING: dict = {
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4o": (0.005, 0.015),
        "gpt-3.5-turbo": (0.0005, 0.0015),
        "claude-3-5-sonnet-20241022": (0.003, 0.015),
        "claude-3-opus-20240229": (0.015, 0.075),
        "gemini-1.5-pro": (0.00125, 0.005),
    }

    def estimate_cost(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Estimate cost in USD for a given token usage.

        Args:
            prompt_tokens: Number of prompt/input tokens.
            completion_tokens: Number of completion/output tokens.

        Returns:
            Estimated cost in USD.
        """
        model_key = self.model.lower()
        if model_key in self._PRICING:
            in_rate, out_rate = self._PRICING[model_key]
        else:
            in_rate, out_rate = 0.01, 0.03
        return (
            prompt_tokens / 1000 * in_rate
            + completion_tokens / 1000 * out_rate
        )


__all__ = ["OracleApiType", "OracleConfig"]
