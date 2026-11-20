"""End-to-end vertical-slice pipeline."""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from oncalldigest.config import SourceConfig, TeamConfig
from oncalldigest.delivery.file import publish
from oncalldigest.models.digest import (
    DigestDocument,
    DigestItem,
    DigestMetadata,
    DigestSection,
    DigestStatus,
    DigestWindow,
    Match,
    SectionSummary,
    SourceHealthSummary,
    Suppression,
)
from oncalldigest.models.signals import SourceHealth, SourceResult
from oncalldigest.models.work_items import WorkItem
from oncalldigest.plugins.base import RunContext
from oncalldigest.processors.aggregate import ProcessedSignal, process
from oncalldigest.sources.log_query import LogQuerySource
from oncalldigest.suppression import apply, load_rules
from oncalldigest.trackers.azure_devops import AzureDevOpsTracker


async def run(config: TeamConfig, output_dir: Path, run_id: str = "local-run") -> DigestDocument:
    context = RunContext(config.team_id, run_id, config.config_revision)
    source_results = await asyncio.gather(
        *[
            _fetch_source(source, context)
            for source in config.sources
            if source.type == "log_query"
        ]
    )
    signals = [signal for result in source_results for signal in result.signals]
    tracker_items: list[WorkItem] = []
    if config.tracker and config.tracker.get("type") == "azure_devops":
        tracker_items = await AzureDevOpsTracker(
            config.tracker["settings"]
        ).list_work_items(context)
    rules_path = Path(config.suppression_file) if config.suppression_file else None
    processed = process(signals, config.sections)
    sections = _sections(processed, config, tracker_items, rules_path)
    health = [_health(result) for result in source_results]
    degraded = any(item.status != "healthy" for item in health)
    now = datetime.now(UTC)
    digest = DigestDocument(
        generated_at=now,
        run_id=run_id,
        team_id=config.team_id,
        window=DigestWindow(start=now - timedelta(days=1), end=now),
        status=DigestStatus(
            overall="degraded" if degraded else "healthy",
            degraded=degraded,
            data_health_banner=(
                "One or more sources failed; results may be incomplete."
                if degraded
                else "All configured sources healthy."
            ),
            source_health=health,
        ),
        sections=sections,
        metadata=DigestMetadata(
            config_revision=config.config_revision,
            processor_version="1",
            source_counts={item.source_id: item.signal_count for item in health},
            mode=(
                "fixture"
                if any(source.settings.get("mode") == "fixture" for source in config.sources)
                else "live"
            ),
        ),
    )
    publish(digest, output_dir)
    return digest


async def _fetch_source(source: SourceConfig, context: RunContext) -> SourceResult:
    """Run a source with bounded retries while preserving source failure health."""
    settings = source.settings.copy()
    settings["timeout_seconds"] = source.timeout_seconds
    plugin = LogQuerySource(source.id, settings)
    last_error = "source failed"
    for attempt in range(source.retries + 1):
        try:
            result = await asyncio.wait_for(
                plugin.fetch(context), timeout=source.timeout_seconds
            )
            if result.health.status != "failed" or attempt == source.retries:
                return result
            last_error = result.health.error or last_error
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt < source.retries:
            await asyncio.sleep(0.1 * (2**attempt))
    return SourceResult(
        health=SourceHealth(
            source_id=source.id,
            status="failed",
            duration_ms=0,
            error=last_error,
        )
    )


def _health(result: SourceResult) -> SourceHealthSummary:
    return SourceHealthSummary.model_validate(result.health.model_dump())


def _sections(
    processed: list[ProcessedSignal],
    config: TeamConfig,
    work_items: list[WorkItem],
    rules_path: Path | None,
) -> list[DigestSection]:
    rules = load_rules(rules_path)
    output: list[DigestSection] = []
    for section in sorted(config.sections, key=lambda item: (item.ordering, item.id)):
        items = [item for item in processed if item.section.id == section.id]
        digest_items: list[DigestItem] = []
        for item in items:
            matches = [
                Match(
                    work_item=work.key,
                    score=1.0,
                    method="exact_identifier",
                    explanation="Signal message matches work-item title.",
                )
                for work in work_items
                if work.title.lower() in item.signal.message.lower()
            ]
            digest_items.append(
                DigestItem(
                    signal=item.signal,
                    fingerprint=item.fingerprint,
                    severity="high" if item.signal.count >= section.threshold * 5 else "medium",
                    suppression=Suppression.model_validate(apply(item.signal, rules)),
                    matches=matches,
                )
            )
        output.append(
            DigestSection(
                id=section.id,
                title=section.title,
                ordering=section.ordering,
                summary=SectionSummary(
                    signal_count=sum(item.signal.count for item in digest_items),
                    affected_components=len({item.signal.component for item in digest_items}),
                    severity_counts={
                        severity: sum(item.severity == severity for item in digest_items)
                        for severity in ("high", "medium", "low")
                        if any(item.severity == severity for item in digest_items)
                    },
                ),
                items=digest_items,
            )
        )
    return output
