"""KQL/ADX log-query source with live and fixture transports."""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from oncalldigest.config import redact_secrets
from oncalldigest.models.signals import Signal, SourceHealth, SourceResult
from oncalldigest.plugins.base import RunContext, Source


class LogQuerySource(Source):
    """Map configured KQL result columns into normalized signals."""

    def __init__(self, source_id: str, settings: dict[str, Any]) -> None:
        self.source_id = source_id
        self.settings = settings

    async def fetch(self, context: RunContext) -> SourceResult:
        started = time.monotonic()
        try:
            rows = await self._rows()
            signals = [self._signal(row) for row in rows]
            health = SourceHealth(
                source_id=self.source_id,
                status="healthy",
                duration_ms=int((time.monotonic() - started) * 1000),
                signal_count=len(signals),
            )
            return SourceResult(signals=signals, health=health)
        except Exception as exc:
            health = SourceHealth(
                source_id=self.source_id,
                status="failed",
                duration_ms=int((time.monotonic() - started) * 1000),
                error=redact_secrets(f"{type(exc).__name__}: {exc}"),
            )
            return SourceResult(health=health)

    async def _rows(self) -> list[dict[str, Any]]:
        mode = self.settings.get("mode", "live")
        if mode == "fixture":
            path = Path(str(self.settings["fixture"]))
            payload = json.loads(path.read_text(encoding="utf-8"))
            return _extract_rows(payload)
        endpoint = str(self.settings["endpoint"])
        database = str(self.settings["database"])
        query = str(self.settings["query"])
        try:
            from azure.identity.aio import DefaultAzureCredential  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "live ADX mode requires the 'azure' optional dependency"
            ) from exc
        credential = DefaultAzureCredential()
        token = await credential.get_token("https://kusto.kusto.windows.net/.default")
        try:
            async with httpx.AsyncClient(
                timeout=float(self.settings.get("timeout_seconds", 30)),
                verify=True,
            ) as client:
                response = await client.post(
                    endpoint.rstrip("/") + "/v2/rest/query",
                    headers={"Authorization": f"Bearer {token.token}"},
                    json={"db": database, "csl": query},
                )
                response.raise_for_status()
                return _extract_rows(cast(dict[str, Any], response.json()))
        finally:
            await credential.close()

    def _signal(self, row: dict[str, Any]) -> Signal:
        now = datetime.now(UTC)
        return Signal(
            kind=str(row["kind"]),
            component=str(row["component"]),
            version=str(row["version"]) if row.get("version") is not None else None,
            environment=str(row["environment"]) if row.get("environment") is not None else None,
            message=str(row["message"]),
            count=max(1, int(row.get("count", 1))),
            first_seen=_timestamp(row.get("first_seen", now)),
            last_seen=_timestamp(row.get("last_seen", now)),
            links=[str(link) for link in row.get("links", [])],
            raw=row,
        )


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
        return cast(list[dict[str, Any]], payload)
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        rows = payload["rows"]
        if all(isinstance(row, dict) for row in rows):
            return cast(list[dict[str, Any]], rows)
    raise ValueError("query response must contain a list of object rows")


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
