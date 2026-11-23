"""Formatting helpers for untrusted investigation output."""

import json
from typing import Any


def wrap_text(value: str) -> str:
    """Mark retrieved text as evidence, never as agent instructions."""
    return f"BEGIN_UNTRUSTED_EVIDENCE\n{value}\nEND_UNTRUSTED_EVIDENCE"


def wrap_json(value: Any) -> str:
    """Serialize and mark a retrieved JSON value as untrusted evidence."""
    return wrap_text(json.dumps(value, sort_keys=True, ensure_ascii=False))
