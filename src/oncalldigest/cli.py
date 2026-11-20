"""Command-line entry point."""

import argparse
import asyncio
import json
from pathlib import Path

from oncalldigest.config import load_config
from oncalldigest.models.digest import DigestDocument
from oncalldigest.pipeline import run


def main() -> int:
    parser = argparse.ArgumentParser(prog="oncalldigest")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("config", type=Path)
    render = subparsers.add_parser("render")
    render.add_argument("--from", dest="digest_path", type=Path, required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    run_parser.add_argument("--run-id", default="local-run")
    subparsers.add_parser("init")
    args = parser.parse_args()

    if args.command == "validate":
        load_config(args.config)
        print(f"valid: {args.config}")
        return 0
    if args.command == "render":
        digest = DigestDocument.model_validate_json(args.digest_path.read_text(encoding="utf-8"))
        print(json.dumps(digest.model_dump(mode="json"), indent=2))
        return 0
    if args.command == "run":
        config = load_config(args.config)
        digest = asyncio.run(run(config, args.output_dir, args.run_id))
        print(f"wrote {len(digest.sections)} sections to {args.output_dir}")
        return 0
    if args.command == "init":
        print("init scaffolding is reserved for Phase 4")
        return 0
    return 2
