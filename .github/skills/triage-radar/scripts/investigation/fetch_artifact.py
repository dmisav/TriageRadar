#!/usr/bin/env python3
"""Read a local build log or test-result artifact without executing it."""

import argparse
from pathlib import Path

from untrusted import wrap_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--max-bytes", type=int, default=20000)
    args = parser.parse_args()
    content = args.artifact.read_bytes()[: args.max_bytes]
    print(wrap_text(content.decode("utf-8", errors="replace")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
