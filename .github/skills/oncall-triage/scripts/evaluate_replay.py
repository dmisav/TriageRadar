#!/usr/bin/env python3
"""Report exact verdict accuracy for replayed triage artifacts."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("actual", type=Path)
    parser.add_argument("expected", type=Path)
    args = parser.parse_args()
    actual = _rows(args.actual)
    expected = _rows(args.expected)
    keys = sorted(set(actual) | set(expected))
    correct = sum(actual.get(key) == expected.get(key) for key in keys)
    accuracy = correct / len(keys) if keys else 1.0
    print(json.dumps({"correct": correct, "total": len(keys), "accuracy": accuracy}))
    return 0 if correct == len(keys) else 1


def _rows(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return {
        row["item_id"]: row["verdict"]["value"]
        for section in document.get("sections", [])
        for row in section.get("rows", [])
    }


if __name__ == "__main__":
    raise SystemExit(main())
