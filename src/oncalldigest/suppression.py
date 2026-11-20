"""Basic, explicitly configured signal suppression."""

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from oncalldigest.models.signals import Signal


class SuppressionRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    substring: str | None = None
    regex: str | None = None
    reason: str = Field(min_length=1)
    work_item: str = Field(min_length=1)
    expires_on: date | None = None


def load_rules(path: Path | None) -> list[SuppressionRule]:
    if path is None or not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("suppression file must contain a YAML list")
    return [SuppressionRule.model_validate(item) for item in data]


def apply(signal: Signal, rules: list[SuppressionRule]) -> dict[str, Any]:
    today = date.today()
    for rule in rules:
        if rule.expires_on is not None and rule.expires_on < today:
            continue
        value = str(getattr(signal, rule.field, signal.raw.get(rule.field, "")))
        matched = rule.substring in value if rule.substring is not None else False
        matched = matched or (
            rule.regex is not None and re.search(rule.regex, value) is not None
        )
        if matched:
            return {
                "state": "suppressed",
                "reason": rule.reason,
                "work_item": rule.work_item,
                "expires_on": (
                    rule.expires_on.isoformat() if rule.expires_on is not None else None
                ),
                "spike_guard_triggered": False,
            }
    return {"state": "active", "spike_guard_triggered": False}
