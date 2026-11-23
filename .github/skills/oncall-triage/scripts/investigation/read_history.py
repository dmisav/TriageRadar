#!/usr/bin/env python3
"""Read bounded history records for a fingerprint or component."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("history", type=Path)
    parser.add_argument("needle")
    args = parser.parse_args()
    records = json.loads(args.history.read_text(encoding="utf-8"))
    needle = args.needle.casefold()
    for record in records:
        if needle in json.dumps(record, sort_keys=True).casefold():
            print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
