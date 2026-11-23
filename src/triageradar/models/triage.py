"""Versioned AI-assisted triage artifact models."""

from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from triageradar.models.signals import Signal


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware UTC values")
    return value.astimezone(UTC)


class TriageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source: str = Field(min_length=1)
    link: str | None = None
    observed_at: datetime

    _observed_at_utc = field_validator("observed_at")(_utc)


class ProposedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "link_existing",
        "comment",
        "new_bug",
        "suppress",
        "rerun",
        "recheck_tomorrow",
        "none",
    ]
    status: Literal["proposed", "approved", "done", "declined"] = "proposed"
    target: str | None = None
    reference: str | None = None
    approval_note: str | None = None


class TriageVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class TriageRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)
    signal: Signal
    evidence: list[TriageEvidence] = Field(min_length=1)
    verdict: TriageVerdict
    proposed_action: ProposedAction
    confidence: float = Field(ge=0, le=1)
    status: Literal["proposed", "approved", "done", "declined"] = "proposed"


class TriageSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    title: str
    ordering: int
    rows: list[TriageRow] = Field(default_factory=list)


class TriageMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_revision: str
    processor_version: str
    agent_id: str | None = None
    evaluation_context: str | None = None


class TriageDocument(BaseModel):
    """Canonical agent-produced triage artifact."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    triage_date: date
    run_id: str
    team_id: str
    digest_path: str
    generated_at: datetime
    sections: list[TriageSection] = Field(default_factory=list)
    metadata: TriageMetadata

    _generated_at_utc = field_validator("generated_at")(_utc)
