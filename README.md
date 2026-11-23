# OnCallDigest

Configurable on-call health digests with an optional AI-assisted triage workflow
for any team or product.

OnCallDigest has two layers:

1. A deterministic core that collects health signals, correlates them with
   existing work items, applies configured processing and suppression rules,
   and emits a versioned `digest.json`.
2. An optional AI-assisted triage layer that investigates the digest,
   consults team-maintained patterns, proposes verdicts and actions, and emits
   a separate `triage-YYYY-MM-DD.json` artifact.

The recommended application workflow is AI-assisted: generate the deterministic
digest, then invoke the triage agent to produce a triage report. The AI layer is
non-deterministic and operates only on top of the deterministic digest. It does
not replace or mutate the core output.

## What is working

The vertical-slice MVP supports a KQL/ADX-style log-query source, read-only
Azure DevOps work items, deterministic aggregation and fingerprinting, basic
suppression, local JSON/HTML output, and a Copilot triage skill. The checked-in
example uses recorded fixtures; live configurations use the same adapters over
HTTPS.

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
uv run oncalldigest run \
  --config examples/minimal.yaml \
  --output-dir ./out \
  --with-ai
```

The command writes `out/digest.json` (the canonical artifact) and
`out/digest.html`, and when `--with-ai` is used it also writes
`out/triage-YYYY-MM-DD.json` and `out/triage-YYYY-MM-DD.html`. Install
`uv sync --extra azure` for live ADX authentication through
`DefaultAzureCredential`.

The `--with-ai` option invokes the command configured by
`ONCALLDIGEST_AI_COMMAND`. The external command must read the supplied
`digest.json` and write the supplied triage JSON artifact. The CLI validates and
renders that artifact before reporting success.

For deterministic-only output, omit `--with-ai`:

```bash
uv run oncalldigest run \
  --config examples/minimal.yaml \
  --output-dir ./out
```

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
oncalldigest run --config CONFIG --output-dir DIRECTORY [--run-id ID] [--with-ai]
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

## AI-assisted triage

The deterministic digest is the input to the triage layer at
[.github/skills/oncall-triage](.github/skills/oncall-triage). There are two
supported ways to run AI-assisted analysis.

### Option 1: External agent, API, or MCP adapter

Use this mode for scheduled or unattended workflows. The configured external
program can call Gemini, OpenAI, Azure OpenAI, an internal model, or an agent
that uses MCP read-only tools.

Configure the adapter command in local `.env` or the production environment:

```dotenv
ONCALLDIGEST_AI_COMMAND=python path/to/triage_agent.py
ONCALLDIGEST_AI_TIMEOUT_SECONDS=900
```

The adapter receives `--config`, `--digest`, and `--output` arguments. It must
read the deterministic digest and write the structured triage artifact:

```bash
uv run oncalldigest run \
  --config examples/full.yaml \
  --output-dir ./out \
  --with-ai
```

This produces:

```text
out/digest.json
out/digest.html
out/triage-YYYY-MM-DD.json
out/triage-YYYY-MM-DD.html
```

The repository defines the adapter contract but does not include a provider
API client. The adapter is responsible for authenticating to the selected AI
provider. Never pass `.env`, tokens, or credentials to the model.

### Option 2: VS Code Copilot interactive mode

Use this mode for interactive investigation and approval in VS Code:

```bash
uv run oncalldigest run \
  --config examples/minimal.yaml \
  --output-dir ./out
```

Then invoke the workspace skill in Copilot Chat:

```text
/oncall-triage
```

Copilot reads `out/digest.json`, follows the team playbook, uses approved
read-only investigation tools, and produces the triage artifact. This mode
uses the Copilot model serving the current VS Code session instead of an
`ONCALLDIGEST_AI_COMMAND` API adapter.

Both modes use the same skill guidance and triage schema. The skill:

1. Reviews digest sections top-down.
2. Looks up known patterns and prior verdicts.
3. Uses read-only investigation helpers.
4. Produces a separate `triage-YYYY-MM-DD.json` artifact.
5. Renders the artifact to HTML after validation.

Validate or render a triage artifact with:

```bash
uv run oncalldigest triage-validate triage-2026-11-20.json
uv run oncalldigest triage-render \
  --from triage-2026-11-20.json \
  --output triage-2026-11-20.html
```

Every verdict must cite evidence. Actions are initially `proposed` and require
explicit approval before execution. The skill never writes to trackers,
comments, suppression files, Git, or remote repositories automatically.

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

## Deterministic core versus AI workflow

The deterministic core is responsible for facts and reproducibility:

- source collection and health status;
- signal normalization;
- thresholds, grouping, and fingerprints;
- tracker lookup;
- suppression rules;
- canonical `digest.json`.

The AI workflow is responsible for interpretation and proposed next steps:

- investigation of evidence;
- known-pattern lookup;
- verdict rationale;
- proposed actions;
- triage report generation.

AI verdicts must cite evidence and remain `proposed` until explicitly approved.
Tracker writes, comments, suppression edits, commits, and pushes are not
performed automatically.

## Design principles

- Product, team, URL, query, and ownership details live in YAML configuration.
- Typed Pydantic models define boundaries between pipeline stages.
- Source failures degrade a run and are represented in the digest health banner.
- Stable ordering, UTC timestamps, and explicit versions make the core output
  reproducible.
- The core does not make LLM calls; AI triage is a separate workflow.