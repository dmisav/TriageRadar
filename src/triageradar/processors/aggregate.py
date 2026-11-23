"""Generic deterministic signal aggregation and fingerprinting."""

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass

from triageradar.config import SectionConfig
from triageradar.models.signals import Signal

_GUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", re.IGNORECASE)
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
_PATH = re.compile(r"(?:[A-Za-z]:)?(?:[/\\][\w .-]+){2,}")


def template(message: str) -> str:
    """Replace volatile identifiers while preserving useful error context."""
    normalized = _GUID.sub("<guid>", message)
    normalized = _PATH.sub("<path>", normalized)
    return _NUMBER.sub("<number>", normalized).strip().lower()


def fingerprint(signal: Signal) -> str:
    """Return a stable hash of component and normalized message template."""
    payload = f"{signal.component}\x00{template(signal.message)}".encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ProcessedSignal:
    signal: Signal
    fingerprint: str
    section: SectionConfig


def process(signals: list[Signal], sections: list[SectionConfig]) -> list[ProcessedSignal]:
    """Threshold, aggregate, fingerprint, and deterministically order signals."""
    result: list[ProcessedSignal] = []
    for section in sorted(sections, key=lambda item: (item.ordering, item.id)):
        grouped: dict[tuple[str, str], list[Signal]] = defaultdict(list)
        for signal in signals:
            if signal.kind not in section.signal_kinds:
                continue
            group_value = str(getattr(signal, section.grouping_key, signal.component))
            grouped[(group_value, template(signal.message))].append(signal)
        for group in grouped.values():
            total = sum(item.count for item in group)
            if total < section.threshold:
                continue
            first = min(item.first_seen for item in group)
            last = max(item.last_seen for item in group)
            merged = group[0].model_copy(
                update={
                    "count": total,
                    "first_seen": first,
                    "last_seen": last,
                    "links": sorted({link for item in group for link in item.links}),
                }
            )
            result.append(ProcessedSignal(merged, fingerprint(merged), section))
    return sorted(
        result,
        key=lambda item: (
            item.section.ordering,
            item.section.id,
            item.fingerprint,
            item.signal.component,
        ),
    )
