"""Normalized signal and source-health models."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Signal(BaseModel):
    """A normalized finding emitted by any source."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(min_length=1)
    component: str = Field(min_length=1)
    version: str | None = None
    environment: str | None = None
    message: str = Field(min_length=1)
    count: int = Field(default=1, ge=1)
    first_seen: datetime
    last_seen: datetime
    links: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("first_seen", "last_seen")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone-aware UTC values")
        return value.astimezone(UTC)


class SourceHealth(BaseModel):
    """Operational status for one source."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    status: Literal["healthy", "degraded", "failed"]
    duration_ms: int = Field(ge=0)
    signal_count: int = Field(default=0, ge=0)
    error: str | None = None


class SourceResult(BaseModel):
    """Source payload plus health information."""

    model_config = ConfigDict(extra="forbid")

    signals: list[Signal] = Field(default_factory=list)
    health: SourceHealth
