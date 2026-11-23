from datetime import UTC, date, datetime
from pathlib import Path

from oncalldigest.models.signals import Signal
from oncalldigest.models.triage import (
    ProposedAction,
    TriageDocument,
    TriageEvidence,
    TriageMetadata,
    TriageRow,
    TriageSection,
    TriageVerdict,
)
from oncalldigest.triage import load, write_html


def _document() -> TriageDocument:
    signal = Signal(
        kind="error",
        component="payments-api",
        message="dependency timeout",
        count=1,
        first_seen=datetime(2026, 11, 20, tzinfo=UTC),
        last_seen=datetime(2026, 11, 20, tzinfo=UTC),
    )
    return TriageDocument(
        triage_date=date(2026, 11, 20),
        run_id="run-1",
        team_id="example-team",
        digest_path="digest.json",
        generated_at=datetime(2026, 11, 20, tzinfo=UTC),
        sections=[
            TriageSection(
                section_id="errors",
                title="Errors",
                ordering=1,
                rows=[
                    TriageRow(
                        item_id="error-1",
                        fingerprint="abc",
                        signal=signal,
                        evidence=[
                            TriageEvidence(
                                kind="log",
                                summary="Seven dependency timeouts observed.",
                                source="ADX",
                                observed_at=datetime(2026, 11, 20, tzinfo=UTC),
                            )
                        ],
                        verdict=TriageVerdict(
                            value="known_pattern",
                            rationale="Matches the documented dependency timeout pattern.",
                        ),
                        proposed_action=ProposedAction(kind="recheck_tomorrow"),
                        confidence=0.9,
                    )
                ],
            )
        ],
        metadata=TriageMetadata(skill_revision="1", processor_version="1"),
    )


def test_triage_artifact_validates_and_renders(tmp_path: Path) -> None:
    source = tmp_path / "triage.json"
    output = tmp_path / "triage.html"
    document = _document()
    source.write_text(document.model_dump_json(), encoding="utf-8")

    loaded = load(source)
    write_html(loaded, output)

    assert "known_pattern" in output.read_text(encoding="utf-8")
    assert "recheck_tomorrow" in output.read_text(encoding="utf-8")
