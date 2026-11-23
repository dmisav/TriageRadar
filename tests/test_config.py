from pathlib import Path

import pytest

from triageradar.config import load_config, redact_secrets


def test_minimal_config_loads() -> None:
    config = load_config(Path("examples/minimal.yaml"))
    assert config.team_id == "example-team"
    assert config.sections[0].grouping_key == "component"


def test_default_and_parenthesized_environment_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "team_id: $(TEAM_ID)\n"
        "config_revision: '1'\n"
        "sources:\n"
        "  - id: source\n"
        "    type: log_query\n"
        "    settings:\n"
        "      endpoint: '${ENDPOINT:-https://example.invalid}'\n"
        "sections: []\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TEAM_ID", "configured-team")

    config = load_config(config_path)

    assert config.team_id == "configured-team"
    assert config.sources[0].settings["endpoint"] == "https://example.invalid"


def test_validation_reports_all_missing_variable_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TEAM_ID", raising=False)
    monkeypatch.delenv("ENDPOINT", raising=False)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "team_id: ${TEAM_ID}\n"
        "config_revision: '1'\n"
        "sources:\n"
        "  - id: source\n"
        "    type: log_query\n"
        "    settings:\n"
        "      endpoint: ${ENDPOINT}\n"
        "sections: []\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ENDPOINT, TEAM_ID"):
        load_config(config_path)


def test_secret_redaction_does_not_expose_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SERVICE_TOKEN", "super-secret-token")
    monkeypatch.setenv("ADX_ENDPOINT", "https://private.example")

    message = redact_secrets("token=super-secret-token endpoint=https://private.example")

    assert "super-secret-token" not in message
    assert "https://private.example" not in message
    assert message.count("***") == 2
