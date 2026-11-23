#!/usr/bin/env python3
"""Print bounded, read-only evidence from a digest."""

import argparse
import json
from pathlib import Path

from untrusted import wrap_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("digest", type=Path)
    args = parser.parse_args()
    document = json.loads(args.digest.read_text(encoding="utf-8"))
    for section in document.get("sections", []):
        for item in section.get("items", []):
            signal = item.get("signal", {})
            print(
                wrap_json(
                    {
                        "section": section.get("id"),
                        "fingerprint": item.get("fingerprint"),
                        "component": signal.get("component"),
                        "message": signal.get("message"),
                        "count": signal.get("count"),
                        "first_seen": signal.get("first_seen"),
                        "last_seen": signal.get("last_seen"),
                        "links": signal.get("links", []),
                    }
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
