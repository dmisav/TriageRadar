"""Small, product-agnostic plugin interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

from triageradar.models.signals import Signal, SourceResult
from triageradar.models.work_items import WorkItem


@dataclass(frozen=True)
class RunContext:
    """Immutable inputs shared by a pipeline run."""

    team_id: str
    run_id: str
    config_revision: str


class Source(ABC):
    """A plugin that fetches and normalizes health signals."""

    source_id: str

    @abstractmethod
    async def fetch(self, context: RunContext) -> SourceResult:
        """Fetch signals and always return an explicit health result."""


class Tracker(ABC):
    """Read-only work-item tracker adapter."""

    tracker_id: str

    @abstractmethod
    async def list_work_items(self, context: RunContext) -> list[WorkItem]:
        """Return configured open/recently-closed work items."""

    @abstractmethod
    async def search_similar(
        self, signal: Signal, context: RunContext
    ) -> list[WorkItem]:
        """Search for work items that may explain a signal."""


class StateStore(Protocol):
    """Durable state with optimistic concurrency."""

    async def load(self, key: str) -> tuple[dict[str, object] | None, str | None]:
        """Load a record and its opaque version token."""

    async def save(
        self, key: str, value: dict[str, object], expected_version: str | None
    ) -> str:
        """Save a record or raise on a stale expected version."""


class Renderer(Protocol):
    """Render the canonical digest into a presentation artifact."""

    async def render(self, digest: object) -> bytes:
        """Render a digest."""


class Delivery(Protocol):
    """Publish a rendered artifact."""

    async def publish(self, artifact: bytes, context: RunContext) -> None:
        """Publish an artifact."""
