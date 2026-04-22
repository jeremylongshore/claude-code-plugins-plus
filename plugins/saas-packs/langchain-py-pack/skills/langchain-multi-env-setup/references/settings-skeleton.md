# Settings Skeleton

The full `Settings` class for a LangChain 1.0 service. Copy, delete the fields
you do not need, add domain-specific ones.

## Full class

```python
from __future__ import annotations
from pathlib import Path
from typing import Literal, Annotated

from pydantic import (
    SecretStr, HttpUrl, Field, ValidationError,
    field_validator, model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Single source of truth for runtime configuration.

    Invariants:
      - Secrets are SecretStr (masked in repr).
      - env is Literal — unknown values rejected at startup.
      - extra="forbid" — typos in env-var names are ValidationErrors.
      - Endpoints are HttpUrl — malformed URLs rejected at startup.
      - No defaults for secrets or the env switch — missing = crash.
    """

    model_config = SettingsConfigDict(
        env_file=None,                 # loader chooses the file per env
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        populate_by_name=True,
    )

    # --- env switch ---
    env: Literal["dev", "staging", "prod"] = Field(..., alias="LANGCHAIN_ENV")

    # --- secrets (always SecretStr) ---
    anthropic_api_key: SecretStr = Field(..., alias="ANTHROPIC_API_KEY")
    openai_api_key: SecretStr | None = Field(None, alias="OPENAI_API_KEY")
    langsmith_api_key: SecretStr = Field(..., alias="LANGSMITH_API_KEY")

    # --- per-env pinning ---
    model_id: str = Field(..., alias="LANGCHAIN_MODEL_ID")
    prompt_commit_hash: str = Field(..., alias="LANGCHAIN_PROMPT_COMMIT")
    vector_index_name: str = Field(..., alias="LANGCHAIN_VECTOR_INDEX")

    # --- endpoints (HttpUrl catches typos) ---
    checkpointer_url: HttpUrl | None = Field(None, alias="LANGCHAIN_CHECKPOINTER_URL")
    otel_endpoint: HttpUrl = Field(..., alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    langsmith_endpoint: HttpUrl = Field(
        "https://api.smith.langchain.com",
        alias="LANGSMITH_ENDPOINT",
    )

    # --- tuning per env ---
    temperature: float = Field(0.2, ge=0.0, le=1.0, alias="LANGCHAIN_TEMPERATURE")
    max_cost_usd_per_day: float = Field(10.0, gt=0, alias="LANGCHAIN_DAILY_BUDGET_USD")
    max_rpm: int = Field(60, gt=0, alias="LANGCHAIN_MAX_RPM")
    otel_sample_rate: float = Field(1.0, ge=0.0, le=1.0, alias="OTEL_SAMPLE_RATE")

    # --- validators ---

    @field_validator("model_id")
    @classmethod
    def _must_be_pinned(cls, v: str) -> str:
        if v in {"latest", "default", ""}:
            raise ValueError(
                f"model_id must be an exact version, not {v!r} — "
                "pinning is required per env"
            )
        return v

    @model_validator(mode="after")
    def _require_checkpointer_in_non_dev(self) -> "Settings":
        if self.env != "dev" and self.checkpointer_url is None:
            raise ValueError(
                "checkpointer_url is required in staging/prod — "
                "MemorySaver loses state on restart"
            )
        return self

    @model_validator(mode="after")
    def _prod_samples_modestly(self) -> "Settings":
        if self.env == "prod" and self.otel_sample_rate > 0.2:
            raise ValueError(
                f"otel_sample_rate={self.otel_sample_rate} too high for prod — "
                "reduce to <= 0.2 head-based sampling"
            )
        return self
```

## Why these invariants

| Invariant | Failure it prevents |
|---|---|
| `SecretStr` for every key | `print(settings)` / `logger.info(settings)` accidentally leaking keys to a log aggregator |
| `Literal["dev","staging","prod"]` on env | Typo (`produciton`) or stray value (`production`) silently falling through to a different branch |
| `extra="forbid"` | `LANGCHIN_MODEL_ID` typo staying unnoticed for months |
| `HttpUrl` for endpoints | `http:/otel:4318` (missing slash) wasting 60s on DNS before the first real call |
| No default for `env` | Deploy without `LANGCHAIN_ENV` set crashes immediately instead of running in the wrong mode |
| `model_id` validator rejects `"latest"` | Silent version drift when the provider rolls a new default |
| `checkpointer_url` required in non-dev | Staging silently running on `MemorySaver` and losing user threads on restart |
| Prod OTEL sample rate ≤ 0.2 | A tuning mistake exporting every trace and blowing the observability bill |

## Why `populate_by_name=True`

Lets you instantiate the class with either the field name
(`Settings(env="dev", ...)`) or the alias (`Settings(LANGCHAIN_ENV="dev", ...)`).
Useful when you pass a dict built from Secret Manager — use the alias form so
the key names match what ops write in the Secret Manager console.

## Testing the class

```python
import os, pytest
from .settings import Settings

def test_missing_api_key_crashes(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("LANGCHAIN_ENV", "prod")
    with pytest.raises(Exception):
        Settings()

def test_typo_rejected(monkeypatch):
    monkeypatch.setenv("LANGCHIN_MODEL_ID", "claude-sonnet-4-6")  # typo
    # extra=forbid → ValidationError
    ...

def test_latest_rejected(monkeypatch):
    monkeypatch.setenv("LANGCHAIN_MODEL_ID", "latest")
    with pytest.raises(ValueError, match="pinning is required"):
        Settings(...)
```

The test suite doubles as documentation — each test describes one failure
mode that the class prevents.

## `model_post_init` vs validators

For anything that **derives** a field from others (`if env == "prod": default_budget = 500`),
use `model_post_init`. For anything that **rejects** an invalid combination,
use `model_validator(mode="after")`. Validators run before the instance is
handed to callers, so invariants hold everywhere downstream.
