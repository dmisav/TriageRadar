"""Entry-point based plugin discovery."""

from importlib.metadata import entry_points
from typing import TypeVar

PluginType = TypeVar("PluginType")


def discover(group: str, expected_type: type[PluginType]) -> dict[str, PluginType]:  # noqa: UP047
    """Load plugins from an entry-point group and validate their shape."""
    discovered: dict[str, PluginType] = {}
    for entry_point in entry_points(group=group):
        plugin = entry_point.load()
        if not isinstance(plugin, type) or not issubclass(plugin, expected_type):
            raise TypeError(
                f"entry point {entry_point.name!r} in {group!r} is not "
                f"a {expected_type.__name__} class"
            )
        discovered[entry_point.name] = plugin()
    return discovered
