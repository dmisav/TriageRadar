"""Configuration loading and validation."""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

_ENV_PATTERN = re.compile(
    r"\$\((?P<paren>[A-Za-z_][A-Za-z0-9_]*)\)|"
    r"\$\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)(?::-?(?P<default>[^}]*))?\}"
)
_SECRET_NAME = re.compile(
    r"(TOKEN|PASSWORD|SECRET|KEY|CONNECTION|WEBHOOK|CLIENT|ENDPOINT)", re.I
)


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
    suppression_file: str | None = None


def _substitute(value: Any) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            name = match.group("paren") or match.group("braced")
            default = match.group("default")
            resolved = os.environ.get(name)
            if resolved:
                return resolved
            if default is not None:
                return default
            raise ValueError(f"environment variable {name!r} is not set or empty")

        return _ENV_PATTERN.sub(replace, value)
    if isinstance(value, list):
        return [_substitute(item) for item in value]
    if isinstance(value, dict):
        return {key: _substitute(item) for key, item in value.items()}
    return value


def _environment_references(value: Any) -> set[tuple[str, str | None]]:
    if isinstance(value, str):
        return {
            (
                match.group("paren") or match.group("braced"),
                match.group("default"),
            )
            for match in _ENV_PATTERN.finditer(value)
        }
    if isinstance(value, list):
        return {reference for item in value for reference in _environment_references(item)}
    if isinstance(value, dict):
        return {
            reference
            for item in value.values()
            for reference in _environment_references(item)
        }
    return set()


def _load_local_env(config_path: Path) -> None:
    """Load local dotenv files only; deployments use the process environment."""
    candidates = (config_path.parent / ".env", Path.cwd() / ".env")
    for candidate in dict.fromkeys(candidates):
        if candidate.is_file():
            load_dotenv(candidate, override=False)


def load_config(path: Path) -> TeamConfig:
    """Load a YAML team configuration with explicit environment substitution."""
    _load_local_env(path)
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError("configuration root must be a YAML mapping")
    missing = sorted(
        name
        for name, default in _environment_references(data)
        if not os.environ.get(name) and default is None
    )
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"missing or empty required environment variables: {names}")
    return TeamConfig.model_validate(_substitute(data))


def config_json_schema() -> dict[str, Any]:
    """Return the JSON Schema generated from the configuration model."""
    return TeamConfig.model_json_schema()


def redact_secrets(message: str) -> str:
    """Redact known secret environment values before logging or displaying errors."""
    redacted = message
    for name, value in os.environ.items():
        if value and len(value) >= 4 and _SECRET_NAME.search(name):
            redacted = redacted.replace(value, "***")
    return redacted
