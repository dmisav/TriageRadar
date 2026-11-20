# ADR 0001: Phase 1 architecture

## Decision

Use a Python 3.12 `src/` project with Pydantic models at every boundary,
entry-point-discovered plugins, and a versioned canonical `digest.json`.

All timestamps in normalized signals and the digest are timezone-aware UTC.
The run context supplies `run_id`, configuration revision, and team identity so
sorting and serialization do not depend on wall-clock calls hidden in workers.

## Consequences

Sources and trackers can use provider SDKs without leaking provider concepts
into the processor. A failed source can be represented as degraded health
without discarding other signals. Renderers and delivery adapters consume the
same canonical artifact and can evolve independently.
