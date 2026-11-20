"""Configuration loading and validation."""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

_ENV_PATTERN = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")


class SectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    ordering: int
    signal_kinds: list[str] = Field(min_length=1)
    threshold: int = Field(default=1, ge=1)
    grouping_key: str = "component"


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    timeout_seconds: float = Field(default=30, gt=0)
    retries: int = Field(default=2, ge=0)
    settings: dict[str, Any] = Field(default_factory=dict)


class TeamConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    team_id: str = Field(min_length=1)
    config_revision: str = Field(min_length=1)
    time_zone: str = "UTC"
    sources: list[SourceConfig] = Field(default_factory=list)
    sections: list[SectionConfig] = Field(default_factory=list)
    tracker: dict[str, Any] | None = None


def _substitute(value: Any) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            resolved = os.environ.get(name)
            if resolved is None:
                raise ValueError(f"environment variable {name!r} is not set")
            return resolved

        return _ENV_PATTERN.sub(replace, value)
    if isinstance(value, list):
        return [_substitute(item) for item in value]
    if isinstance(value, dict):
        return {key: _substitute(item) for key, item in value.items()}
    return value


def load_config(path: Path) -> TeamConfig:
    """Load a YAML team configuration with explicit environment substitution."""
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError("configuration root must be a YAML mapping")
    return TeamConfig.model_validate(_substitute(data))


def config_json_schema() -> dict[str, Any]:
    """Return the JSON Schema generated from the configuration model."""
    return TeamConfig.model_json_schema()
