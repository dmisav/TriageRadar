#!/usr/bin/env python3
"""Append only approved triage verdict summaries to known patterns."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("triage_json", type=Path)
    parser.add_argument("--known-patterns", type=Path, required=True)
    args = parser.parse_args()
    document = json.loads(args.triage_json.read_text(encoding="utf-8"))
    entries: list[str] = []
    for section in document.get("sections", []):
        for row in section.get("rows", []):
            action = row.get("proposed_action", {})
            if row.get("status") not in {"approved", "done"}:
                continue
            if action.get("status") not in {"approved", "done"}:
                continue
            evidence = row.get("evidence", [])
            links = ", ".join(item.get("link", "") for item in evidence if item.get("link"))
            entries.append(
                "\n### Approved entry: "
                + str(row["item_id"])
                + "\n\n"
                + f"- Verdict: {row['verdict']['value']}\n"
                + f"- Rationale: {row['verdict']['rationale']}\n"
                + f"- Evidence: {links or 'recorded in triage artifact'}\n"
            )
    if entries:
        with args.known_patterns.open("a", encoding="utf-8") as file:
            file.write("\n".join(entries))
    print(f"appended {len(entries)} approved learning entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
