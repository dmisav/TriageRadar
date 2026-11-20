# OnCallDigest

Configurable, deterministic on-call health digests for any team or product.

OnCallDigest collects health signals from configured sources, correlates them
with existing work items, applies deterministic processing and suppression
rules, and emits a versioned `digest.json`. Rendering, delivery, and AI
triage are separate layers.

## What is working

The vertical-slice MVP supports a KQL/ADX-style log-query source, read-only
Azure DevOps work items, deterministic aggregation and fingerprinting, basic
suppression, and local JSON/HTML output. The checked-in example uses recorded
fixtures; live configurations use the same adapters over HTTPS.

The current example demonstrates:

- A log-query source with recorded error rows
- Aggregation of repeated error templates
- A read-only Azure DevOps work-item match
- A configured suppression rule
- A healthy-source data banner
- Canonical JSON and HTML reports

## Quick start

```bash
uv sync --extra dev
uv run oncalldigest validate examples/minimal.yaml
uv run oncalldigest run --config examples/minimal.yaml --output-dir ./out
```

The command writes `out/digest.json` (the canonical artifact) and
`out/digest.html`. Install `uv sync --extra azure` for live ADX authentication
through `DefaultAzureCredential`.

To open the generated HTML locally:

```bash
python3 -m http.server 8765 --directory ./out
```

Then open <http://127.0.0.1:8765/digest.html>.

To render and validate an existing digest:

```bash
uv run oncalldigest render --from ./out/digest.json
```

## CLI

```text
oncalldigest validate CONFIG
oncalldigest run --config CONFIG --output-dir DIRECTORY [--run-id ID]
oncalldigest render --from DIGEST_JSON
```

`validate` loads dotenv values for local development, resolves environment
references, validates the YAML model, and reports missing variable names
without exposing values.

## Configuration and secrets

Keep team behavior in the tracked YAML configuration. Reference deployment
values with `$(VAR)` or `${VAR:-default}`; do not put endpoints, tokens,
connection strings, tenant IDs, or recipients directly in YAML. Copy
[.env.example](.env.example) to a local `.env` for development only.

`oncalldigest validate` reports every missing or empty required variable by
name, never its value. Production deployments should inject the same variables
through runtime environment, Key Vault references, pipeline secrets, or
container secrets. The image must not contain a `.env` file.

Use [examples/minimal.yaml](examples/minimal.yaml) for an offline fixture-backed
run and [examples/full.yaml](examples/full.yaml) as a live configuration
starting point. Suppression rules are kept separately in
[examples/suppressions.yaml](examples/suppressions.yaml).

See [docs/onboard-new-team.md](docs/onboard-new-team.md) for team setup,
[docs/architecture.md](docs/architecture.md) for runtime architecture and data
flow, and [docs/adr/0001-phase-one-architecture.md](docs/adr/0001-phase-one-architecture.md)
for the initial architecture decisions.

## Output contract

`digest.json` is the canonical, versioned output. Its structure is defined by
[schemas/digest.v1.schema.json](schemas/digest.v1.schema.json) and represented
at runtime by the typed models in
[src/oncalldigest/models/digest.py](src/oncalldigest/models/digest.py).

The HTML report is derived from the JSON artifact, so downstream integrations
can consume the structured output without scraping HTML.

## Development

Install the development environment and run all checks:

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy src tests
uv run pytest
```

The test suite includes unit tests, processing/pipeline tests, and a CLI
end-to-end test that runs the application with recorded fixtures and verifies
the generated JSON and HTML reports.

## Project layout

```text
src/oncalldigest/
  cli.py                 CLI commands
  config.py              YAML, dotenv, environment references, redaction
  pipeline.py            End-to-end orchestration
  models/                Typed signal, work-item, and digest contracts
  sources/               Signal source adapters
  trackers/              Read-only work-item adapters
  processors/            Generic aggregation and fingerprinting
  suppression.py         YAML suppression rules
  rendering/             HTML renderer
  delivery/              Atomic file delivery
tests/                   Unit, integration, and CLI end-to-end tests
examples/                Minimal/full configs and suppression rules
fixtures/                Recorded source and tracker responses
schemas/                 JSON Schemas for config and digest output
docs/                    Architecture, ADRs, and onboarding guidance
```

## Current limitations and roadmap

The following are planned extensions:

- Fingerprint-label and fuzzy-title matching
- Spike guards and persistent StateStore implementations
- CI pipeline and test-result sources
- SMTP and Teams/Slack delivery adapters
- Grafana/dashboard sources
- GitHub Issues and Jira trackers
- Container images and scheduled deployment manifests

The core intentionally does not create or modify work items and does not make
LLM calls.

## Design principles

- Product, team, URL, query, and ownership details live in YAML configuration.
- Typed Pydantic models define boundaries between pipeline stages.
- Source failures degrade a run and are represented in the digest health banner.
- Stable ordering, UTC timestamps, and explicit versions make output reproducible.
- The core does not make LLM calls.