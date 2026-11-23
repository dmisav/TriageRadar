"""Self-contained, responsive HTML digest renderer."""

from html import escape

from triageradar.models.digest import DigestDocument, DigestItem


def render(digest: DigestDocument) -> str:
    total_signals = sum(
        item.signal.count for section in digest.sections for item in section.items
    )
    affected_components = len(
        {
            item.signal.component
            for section in digest.sections
            for item in section.items
        }
    )
    source_count = len(digest.status.source_health)
    health_class = "healthy" if not digest.status.degraded else "degraded"
    sections: list[str] = []
    for section in digest.sections:
        rows = "".join(_item_row(item) for item in section.items)
        empty = (
            rows
            if rows
            else "<tr><td class='empty' colspan='6'>No signals in this section.</td></tr>"
        )
        sections.append(
            f"<section class='section-card'>"
            f"<div class='section-heading'><div><span class='eyebrow'>SECTION "
            f"{section.ordering:02d}</span><h2>{escape(section.title)}</h2></div>"
            f"<span class='section-count'>{len(section.items)} items</span></div>"
            "<div class='table-wrap'><table><thead><tr>"
            "<th>Signal</th><th>Component</th><th>Severity</th><th>Count</th>"
            "<th>Window</th><th>Disposition</th>"
            f"</tr></thead><tbody>{empty}</tbody></table></div></section>"
        )
    source_health = "".join(
        f"<li><span class='health-dot {escape(source.status)}'></span>"
        f"{escape(source.source_id)} <span class='source-status'>"
        f"{escape(source.status)}</span></li>"
        for source in digest.status.source_health
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(digest.team_id)} · TriageRadar</title>"
        "<style>"
        ":root{color-scheme:light;--ink:#172033;--muted:#667085;--line:#e6eaf0;"
        "--surface:#fff;--canvas:#f5f7fb;--blue:#315eea;--blue-soft:#eef2ff;"
        "--red:#c93636;--red-soft:#fff0f0;--amber:#a15c00;--amber-soft:#fff7e6;"
        "--green:#18794e;--green-soft:#eaf8f0}"
        "*{box-sizing:border-box}body{margin:0;background:var(--canvas);color:var(--ink);"
        "font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"
        "'Segoe UI',sans-serif;line-height:1.5}.shell{max-width:1180px;margin:0 auto;"
        "padding:32px 20px 56px}.hero{background:linear-gradient(135deg,#182451,#315eea);"
        "color:#fff;border-radius:20px;padding:32px;box-shadow:0 12px 30px #1f3a8a26}"
        ".brand{font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:.76;"
        "font-weight:700}.hero h1{font-size:clamp(28px,5vw,46px);margin:8px 0 4px;"
        "letter-spacing:-.04em}.hero p{margin:0;color:#dbe4ff}.hero-meta{display:flex;"
        "gap:10px;flex-wrap:wrap;margin-top:24px}.pill{display:inline-flex;align-items:center;"
        "gap:7px;border-radius:999px;padding:7px 12px;font-size:13px;font-weight:700;"
        "background:#ffffff1f;color:#fff}.health-pill{background:#ffffff2b}.health-pill.degraded"
        "{background:#ffcf5c;color:#4a2d00}.health-dot{display:inline-block;width:8px;"
        "height:8px;border-radius:50%;background:#79e2a8}.health-dot.degraded{background:#f6b73c}"
        ".health-dot.failed{background:#ff8585}.dashboard{display:grid;grid-template-columns:"
        "repeat(3,1fr);gap:14px;margin:20px 0}.metric,.health-card,.section-card{background:"
        "var(--surface);border:1px solid var(--line);border-radius:16px;"
        "box-shadow:0 5px 16px #17203308}"
        ".metric{padding:18px 20px}.metric-label,.eyebrow{font-size:11px;font-weight:800;"
        "letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}.metric-value{font-size:30px;"
        "font-weight:800;margin-top:3px}.health-card{padding:18px 20px;margin-bottom:20px}"
        ".health-card h2{font-size:15px;margin:0 0 10px}.health-card ul{display:flex;"
        "flex-wrap:wrap;gap:12px 24px;padding:0;margin:0;list-style:none;color:var(--muted);"
        "font-size:13px}.source-status{margin-left:4px;color:var(--ink);font-weight:700}"
        ".section-card{margin-top:20px;overflow:hidden}.section-heading{display:flex;"
        "justify-content:space-between;align-items:center;padding:20px 22px 16px}"
        ".section-heading h2{"
        "font-size:21px;margin:3px 0 0;letter-spacing:-.02em}.section-count{font-size:13px;"
        "color:var(--muted);background:var(--canvas);padding:6px 10px;border-radius:999px}"
        ".table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:780px}"
        "th{background:#fafbfc;color:var(--muted);font-size:11px;letter-spacing:.08em;"
        "text-transform:uppercase;text-align:left;padding:11px 20px;"
        "border-top:1px solid var(--line);"
        "border-bottom:1px solid var(--line)}td{padding:16px 20px;"
        "border-bottom:1px solid var(--line);"
        "vertical-align:top;font-size:14px}tbody tr:last-child td{border-bottom:0}.signal-message{"
        "font-weight:700;max-width:370px}.signal-link{display:inline-block;margin-top:5px;"
        "font-size:12px;color:var(--blue);text-decoration:none}.component{color:var(--muted)}"
        ".badge{display:inline-block;border-radius:999px;padding:4px 9px;font-size:12px;"
        "font-weight:800;text-transform:capitalize}.severity-high{color:var(--red);background:var(--red-soft)}"
        ".severity-medium{color:var(--amber);background:var(--amber-soft)}.severity-low{"
        "color:var(--green);background:var(--green-soft)}.disposition-suppressed{color:var(--amber);"
        "background:var(--amber-soft)}.disposition-active{color:var(--blue);background:var(--blue-soft)}"
        ".disposition-resurfaced{color:var(--red);background:var(--red-soft)}.detail{display:block;"
        "color:var(--muted);font-size:12px;margin-top:5px}.empty{text-align:center;color:var(--muted);"
        "padding:30px}.footer{color:var(--muted);font-size:12px;text-align:center;margin-top:26px}"
        "@media(max-width:700px){.shell{padding:18px 12px 40px}.hero{padding:24px 20px}"
        ".dashboard{grid-template-columns:1fr}.section-heading{padding:17px}"
        ".section-heading h2{font-size:18px}"
        "th,td{padding-left:14px;padding-right:14px}}"
        "</style></head><body><main class='shell'>"
        f"<header class='hero'><div class='brand'>TriageRadar · Daily health digest</div>"
        f"<h1>{escape(digest.team_id)}</h1>"
        f"<p>{escape(digest.window.start.strftime('%b %d, %Y'))} · "
        f"{escape(digest.status.data_health_banner)}</p>"
        f"<div class='hero-meta'><span class='pill health-pill {health_class}'>"
        f"<span class='health-dot {health_class}'></span>{escape(digest.status.overall)}"
        f"</span><span class='pill'>Run {escape(digest.run_id)}</span>"
        f"<span class='pill'>Generated {escape(digest.generated_at.strftime('%H:%M UTC'))}</span>"
        "</div></header>"
        f"<div class='dashboard'><div class='metric'><div class='metric-label'>Signals</div>"
        f"<div class='metric-value'>{total_signals}</div></div>"
        f"<div class='metric'><div class='metric-label'>Components</div>"
        f"<div class='metric-value'>{affected_components}</div></div>"
        f"<div class='metric'><div class='metric-label'>Sources</div>"
        f"<div class='metric-value'>{source_count}</div></div></div>"
        f"<div class='health-card'><h2>Data health</h2><ul>{source_health}</ul></div>"
        + "".join(sections)
        + f"<div class='footer'>Processor {escape(digest.metadata.processor_version)}"
        f" · Config revision {escape(digest.metadata.config_revision)}</div>"
        "</main></body></html>"
    )


def _item_row(item: DigestItem) -> str:
    """Render one typed digest item without allowing content to become markup."""
    signal = item.signal
    suppression = item.suppression
    severity = item.severity if item.severity in {"high", "medium", "low"} else "low"
    state = suppression.state
    links = "".join(
        f"<a class='signal-link' href='{escape(link, quote=True)}' target='_blank' "
        f"rel='noopener noreferrer'>View evidence ↗</a>"
        for link in signal.links[:1]
    )
    detail = (
        escape(suppression.reason)
        if suppression.reason
        else "No suppression applied"
    )
    return (
        "<tr>"
        f"<td><div class='signal-message'>{escape(signal.message)}</div>{links}</td>"
        f"<td><span class='component'>{escape(signal.component)}</span></td>"
        f"<td><span class='badge severity-{severity}'>{escape(severity)}</span></td>"
        f"<td><strong>{signal.count}</strong></td>"
        f"<td><span class='detail'>{escape(signal.first_seen.strftime('%H:%M UTC'))}"
        f" – {escape(signal.last_seen.strftime('%H:%M UTC'))}</span></td>"
        f"<td><span class='badge disposition-{escape(state)}'>{escape(state)}</span>"
        f"<span class='detail'>{detail}</span></td>"
        "</tr>"
    )
