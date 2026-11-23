#!/usr/bin/env python3
"""Search a recorded work-item response without modifying it."""

import argparse
import json
from pathlib import Path

from untrusted import wrap_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_items", type=Path)
    parser.add_argument("needle")
    args = parser.parse_args()
    items = json.loads(args.work_items.read_text(encoding="utf-8"))
    needle = args.needle.casefold()
    for item in items:
        haystack = " ".join(
            str(item.get(field, "")) for field in ("key", "title", "description", "status")
        )
        if needle in haystack.casefold():
            print(wrap_json(item))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
