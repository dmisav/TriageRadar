"""Work-item models shared by tracker plugins and matching."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkItem(BaseModel):
    """Read-only representation of a tracker work item."""

    model_config = ConfigDict(extra="forbid")

    tracker: str = Field(min_length=1)
    key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    url: str | None = None
    labels: list[str] = Field(default_factory=list)
    status: str = Field(min_length=1)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
