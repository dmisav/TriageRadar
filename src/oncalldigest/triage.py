"""Triage artifact validation and safe HTML rendering."""

from html import escape
from pathlib import Path

from oncalldigest.models.triage import TriageDocument


def load(path: Path) -> TriageDocument:
    """Load and validate a triage artifact, including its evidence guardrail."""
    document = TriageDocument.model_validate_json(path.read_text(encoding="utf-8"))
    for section in document.sections:
        for row in section.rows:
            if not row.evidence:
                raise ValueError(f"triage row {row.item_id!r} has no evidence")
    return document


def render(document: TriageDocument) -> str:
    """Render a triage artifact as escaped, static HTML."""
    rows: list[str] = []
    for section in sorted(document.sections, key=lambda item: (item.ordering, item.section_id)):
        for row in section.rows:
            evidence = "<br>".join(
                escape(item.summary) for item in row.evidence
            )
            rows.append(
                "<tr>"
                f"<td>{escape(section.title)}</td>"
                f"<td>{escape(row.signal.component)}: {escape(row.signal.message)}</td>"
                f"<td>{escape(evidence)}</td>"
                f"<td>{escape(row.verdict.value)}</td>"
                f"<td>{escape(row.proposed_action.kind)} "
                f"({escape(row.proposed_action.status)})</td>"
                "</tr>"
            )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>AI-assisted triage</title>"
        "<style>body{font-family:system-ui;margin:2rem}table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #ccc;padding:.5rem;text-align:left;vertical-align:top}</style>"
        "</head><body>"
        f"<h1>{escape(document.team_id)} triage for {document.triage_date}</h1>"
        "<p>All actions remain subject to explicit approval.</p>"
        "<table><thead><tr><th>Item</th><th>Signal</th><th>Evidence</th>"
        "<th>Verdict</th><th>Proposed action</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></body></html>"
    )


def write_html(document: TriageDocument, output: Path) -> None:
    output.write_text(render(document), encoding="utf-8")
