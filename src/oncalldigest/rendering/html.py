"""Minimal escaped HTML renderer with a data-health banner."""

from html import escape

from oncalldigest.models.digest import DigestDocument


def render(digest: DigestDocument) -> str:
    sections: list[str] = []
    for section in digest.sections:
        items = "".join(
            f"<li><strong>{escape(item.severity)}</strong> "
            f"{escape(item.signal.component)}: {escape(item.signal.message)} "
            f"(count {item.signal.count})</li>"
            for item in section.items
        )
        sections.append(f"<section><h2>{escape(section.title)}</h2><ul>{items}</ul></section>")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>On-call digest</title></head><body>"
        f"<header><h1>{escape(digest.team_id)} on-call digest</h1>"
        f"<p>{escape(digest.status.data_health_banner)}</p></header>"
        + "".join(sections)
        + "</body></html>"
    )
