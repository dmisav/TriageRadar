import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_run_generates_digest_and_html_report(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "report"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository_root / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "triageradar.cli",
            "run",
            "--config",
            "examples/minimal.yaml",
            "--output-dir",
            str(output_dir),
            "--run-id",
            "e2e-test",
            "--no-open",
        ],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "wrote 1 sections" in completed.stdout

    digest_path = output_dir / "digest.json"
    html_path = output_dir / "digest.html"
    assert digest_path.is_file()
    assert html_path.is_file()

    digest = json.loads(digest_path.read_text(encoding="utf-8"))
    html = html_path.read_text(encoding="utf-8")
    item = digest["sections"][0]["items"][0]

    assert digest["run_id"] == "e2e-test"
    assert digest["status"]["overall"] == "healthy"
    assert item["signal"]["component"] == "payments-api"
    assert item["suppression"]["state"] == "suppressed"
    assert item["matches"][0]["work_item"] == "PAY-123"
    assert "example-team" in html
    assert "TriageRadar" in html
    assert "Known dependency maintenance window" in html
