# OnCallDigest

Configurable, deterministic on-call health digests for any team or product.

OnCallDigest collects health signals from configured sources, correlates them
with existing work items, applies deterministic processing and suppression
rules, and emits a versioned `digest.json`. Rendering, delivery, and AI
triage are separate layers.

## Status

Phase 1 establishes the typed contracts, configuration model, canonical digest
schema, plugin interfaces, CLI, CI, and onboarding documentation. Collection
sources and tracker adapters are introduced in later phases.

## Quick start

```bash
uv sync --extra dev
uv run oncalldigest validate examples/minimal.yaml
uv run oncalldigest init ./team-config
```

See [docs/onboard-new-team.md](docs/onboard-new-team.md) for configuration
guidance and [docs/adr/0001-phase-one-architecture.md](docs/adr/0001-phase-one-architecture.md)
for the architecture decisions behind the initial contracts.

## Design principles

- Product, team, URL, query, and ownership details live in YAML configuration.
- Typed Pydantic models define boundaries between pipeline stages.
- Source failures degrade a run and are represented in the digest health banner.
- Stable ordering, UTC timestamps, and explicit versions make output reproducible.
- The core does not make LLM calls.