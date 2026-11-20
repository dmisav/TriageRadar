"""Canonical digest.json v1 models."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from oncalldigest.models.signals import Signal


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware UTC values")
    return value.astimezone(UTC)


class DigestWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: datetime
    end: datetime
    time_zone: Literal["UTC"] = "UTC"

    _start_utc = field_validator("start")(_utc)
    _end_utc = field_validator("end")(_utc)


class SourceHealthSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    status: Literal["healthy", "degraded", "failed"]
    duration_ms: int = Field(ge=0)
    signal_count: int = Field(ge=0)
    error: str | None = None


class DigestStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall: Literal["healthy", "degraded", "failed"]
    degraded: bool
    data_health_banner: str
    source_health: list[SourceHealthSummary] = Field(default_factory=list)


class Suppression(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["active", "suppressed", "resurfaced"] = "active"
    reason: str | None = None
    work_item: str | None = None
    expires_on: datetime | None = None
    spike_guard_triggered: bool = False


class Match(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_item: str
    score: float = Field(ge=0, le=1)
    method: Literal["fingerprint", "exact_identifier", "fuzzy_title"]
    explanation: str = Field(min_length=1)


class DigestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal: Signal
    fingerprint: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    suppression: Suppression = Field(default_factory=Suppression)
    matches: list[Match] = Field(default_factory=list)


class SectionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_count: int = Field(ge=0)
    affected_components: int = Field(ge=0)
    severity_counts: dict[str, int] = Field(default_factory=dict)


class DigestSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    ordering: int
    summary: SectionSummary
    items: list[DigestItem] = Field(default_factory=list)


class DigestMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_revision: str
    processor_version: str
    source_counts: dict[str, int] = Field(default_factory=dict)
    mode: str = "live"


class DigestDocument(BaseModel):
    """Versioned canonical artifact consumed by renderers and future agents."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    generated_at: datetime
    run_id: str
    team_id: str
    window: DigestWindow
    status: DigestStatus
    sections: list[DigestSection] = Field(default_factory=list)
    metadata: DigestMetadata

    _generated_at_utc = field_validator("generated_at")(_utc)
