from pathlib import Path

from oncalldigest.config import load_config


def test_minimal_config_loads() -> None:
    config = load_config(Path("examples/minimal.yaml"))
    assert config.team_id == "example-team"
    assert config.sections[0].grouping_key == "component"
