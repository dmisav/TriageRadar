# OnCallDigest

Configurable, deterministic on-call health digests for any team or product.

OnCallDigest collects health signals from configured sources, correlates them
with existing work items, applies deterministic processing and suppression
rules, and emits a versioned `digest.json`. Rendering, delivery, and AI
triage are separate layers.

## Status

The vertical-slice MVP supports a KQL/ADX-style log-query source, read-only
Azure DevOps work items, deterministic aggregation and fingerprinting, basic
suppression, and local JSON/HTML output. The checked-in example uses recorded
fixtures; live configurations use the same adapters over HTTPS.

## Quick start

```bash
uv sync --extra dev
uv run oncalldigest validate examples/minimal.yaml
uv run oncalldigest run --config examples/minimal.yaml --output-dir ./out
```

The command writes `out/digest.json` (the canonical artifact) and
`out/digest.html`. Install `uv sync --extra azure` for live ADX authentication
through `DefaultAzureCredential`.

See [docs/onboard-new-team.md](docs/onboard-new-team.md) for configuration
guidance and [docs/adr/0001-phase-one-architecture.md](docs/adr/0001-phase-one-architecture.md)
for the architecture decisions behind the initial contracts.

## Design principles

- Product, team, URL, query, and ownership details live in YAML configuration.
- Typed Pydantic models define boundaries between pipeline stages.
- Source failures degrade a run and are represented in the digest health banner.
- Stable ordering, UTC timestamps, and explicit versions make output reproducible.
- The core does not make LLM calls.