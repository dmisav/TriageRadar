"""Read-only Azure DevOps work-item tracker."""

import base64
import json
import os
from pathlib import Path
from typing import Any

import httpx

from oncalldigest.models.work_items import WorkItem
from oncalldigest.plugins.base import RunContext, Tracker


class AzureDevOpsTracker(Tracker):
    """Fetch configured Azure DevOps work items without write operations."""

    def __init__(self, settings: dict[str, Any]) -> None:
        self.tracker_id = "azure_devops"
        self.settings = settings

    async def list_work_items(self, context: RunContext) -> list[WorkItem]:
        if self.settings.get("mode", "live") == "fixture":
            payload = json.loads(
                Path(str(self.settings["fixture"])).read_text(encoding="utf-8")
            )
            return [WorkItem.model_validate(item) for item in payload]
        organization = str(self.settings["organization"])
        project = str(self.settings["project"])
        query = str(self.settings["wiql"])
        token = os.environ.get(str(self.settings["token_env"]))
        if not token:
            raise ValueError("Azure DevOps token environment variable is not set")
        basic = base64.b64encode(f":{token}".encode()).decode()
        base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        async with httpx.AsyncClient(timeout=30, verify=True) as client:
            response = await client.post(
                f"{base_url}/wit/wiql?api-version=7.1",
                headers={"Authorization": f"Basic {basic}"},
                json={"query": query},
            )
            response.raise_for_status()
            ids = [int(item["id"]) for item in response.json().get("workItems", [])]
            if not ids:
                return []
            details = await client.get(
                f"{base_url}/wit/workitems",
                params={"ids": ",".join(str(item) for item in ids), "api-version": "7.1"},
                headers={"Authorization": f"Basic {basic}"},
            )
            details.raise_for_status()
            return [_work_item(item) for item in details.json().get("value", [])]

    async def search_similar(
        self, signal: Any, context: RunContext
    ) -> list[WorkItem]:
        items = await self.list_work_items(context)
        needle = str(signal.message).lower()
        return [item for item in items if needle in item.title.lower()]


def _work_item(item: dict[str, Any]) -> WorkItem:
    fields = item.get("fields", {})
    return WorkItem(
        tracker="azure_devops",
        key=str(item["id"]),
        title=str(fields.get("System.Title", "")),
        description=str(fields.get("System.Description", "")),
        url=str(item.get("url")) if item.get("url") else None,
        labels=[str(fields.get("System.Tags", ""))] if fields.get("System.Tags") else [],
        status=str(fields.get("System.State", "Unknown")),
    )
