from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── YAML-backed models ────────────────────────────────────────────────────────

class ServerConfig(BaseModel):
    ssh_host: str
    description: str = ""
    tags: list[str] = []


class LLMConfig(BaseModel):
    model: str = "anthropic/claude-3.5-haiku"
    temperature: float = 0.2


class AppConfig(BaseModel):
    llm: LLMConfig = LLMConfig()
    servers: dict[str, ServerConfig] = {}


# ── Secret settings from .env ─────────────────────────────────────────────────

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_token: str
    openrouter_api_key: str
    allowed_user_ids: list[int] = []

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_user_ids(cls, v: object) -> list[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v  # type: ignore[return-value]


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_app_config(path: Path | None = None) -> AppConfig:
    """Load config.yaml. Path defaults to config.yaml next to this file."""
    config_path = path or Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {config_path}. "
            "Copy config.yaml.example and fill in your servers."
        )
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig.model_validate(data or {})


settings = Settings()
app_config = load_app_config()
