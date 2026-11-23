#!/usr/bin/env python3
"""Validate and render a triage artifact without performing external writes."""

import argparse
import sys
from pathlib import Path

repository_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository_root / "src"))

from oncalldigest.triage import load, write_html  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("triage_json", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = load(args.triage_json)
    write_html(document, args.output)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
