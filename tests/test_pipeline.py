import json
from pathlib import Path

from triageradar.config import load_config
from triageradar.pipeline import run


def test_example_run_writes_digest_and_html(tmp_path: Path) -> None:
    config = load_config(Path("examples/minimal.yaml"))
    digest = __import__("asyncio").run(run(config, tmp_path, "test-run"))

    payload = json.loads((tmp_path / "digest.json").read_text(encoding="utf-8"))
    assert payload["run_id"] == "test-run"
    assert payload["sections"][0]["items"][0]["suppression"]["state"] == "suppressed"
    assert payload["sections"][0]["items"][0]["matches"][0]["work_item"] == "PAY-123"
    assert "data-health" not in (tmp_path / "digest.html").read_text(encoding="utf-8")
    assert digest.status.overall == "healthy"
