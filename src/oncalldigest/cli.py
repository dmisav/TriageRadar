"""Command-line entry point."""

import argparse
import asyncio
import json
import os
import shlex
import subprocess
from pathlib import Path

from oncalldigest.config import load_config, redact_secrets
from oncalldigest.models.digest import DigestDocument
from oncalldigest.pipeline import run
from oncalldigest.triage import load as load_triage
from oncalldigest.triage import write_html


def main() -> int:
    parser = argparse.ArgumentParser(prog="oncalldigest")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("config", type=Path)
    render = subparsers.add_parser("render")
    render.add_argument("--from", dest="digest_path", type=Path, required=True)
    triage_validate = subparsers.add_parser("triage-validate")
    triage_validate.add_argument("triage_path", type=Path)
    triage_render = subparsers.add_parser("triage-render")
    triage_render.add_argument("--from", dest="triage_path", type=Path, required=True)
    triage_render.add_argument("--output", type=Path, required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    run_parser.add_argument("--run-id", default="local-run")
    run_parser.add_argument(
        "--with-ai",
        action="store_true",
        help="invoke the configured external triage agent after generating the digest",
    )
    subparsers.add_parser("init")
    args = parser.parse_args()

    if args.command == "validate":
        try:
            load_config(args.config)
        except (OSError, ValueError) as exc:
            print(f"invalid configuration: {redact_secrets(str(exc))}")
            return 2
        print(f"valid: {args.config}")
        return 0
    if args.command == "render":
        digest = DigestDocument.model_validate_json(args.digest_path.read_text(encoding="utf-8"))
        print(json.dumps(digest.model_dump(mode="json"), indent=2))
        return 0
    if args.command == "triage-validate":
        load_triage(args.triage_path)
        print(f"valid: {args.triage_path}")
        return 0
    if args.command == "triage-render":
        document = load_triage(args.triage_path)
        write_html(document, args.output)
        print(f"wrote {args.output}")
        return 0
    if args.command == "run":
        try:
            config = load_config(args.config)
            digest = asyncio.run(run(config, args.output_dir, args.run_id))
            if args.with_ai:
                _run_ai_triage(
                    args.config, args.output_dir, digest.generated_at.date().isoformat()
                )
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            print(f"run failed: {redact_secrets(str(exc))}")
            return 2
        print(f"wrote {len(digest.sections)} sections to {args.output_dir}")
        return 0
    if args.command == "init":
        print("init scaffolding is reserved for Phase 4")
        return 0
    return 2


def _run_ai_triage(config_path: Path, output_dir: Path, triage_date: str) -> None:
    """Invoke an explicitly configured external agent and validate its artifact."""
    command_template = os.environ.get("ONCALLDIGEST_AI_COMMAND")
    if not command_template:
        raise ValueError(
            "--with-ai requires ONCALLDIGEST_AI_COMMAND; "
            "use the oncall-triage Copilot skill or configure an agent command"
        )
    digest_path = output_dir / "digest.json"
    triage_path = output_dir / f"triage-{triage_date}.json"
    command = [
        argument.format(
            config=str(config_path),
            digest=str(digest_path),
            output=str(triage_path),
        )
        for argument in shlex.split(command_template)
    ]
    command.extend(
        [
            "--config",
            str(config_path),
            "--digest",
            str(digest_path),
            "--output",
            str(triage_path),
        ]
    )
    timeout = float(os.environ.get("ONCALLDIGEST_AI_TIMEOUT_SECONDS", "900"))
    completed = subprocess.run(command, timeout=timeout, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"AI triage command failed with exit code {completed.returncode}")
    document = load_triage(triage_path)
    write_html(document, output_dir / f"triage-{triage_date}.html")


if __name__ == "__main__":
    raise SystemExit(main())
