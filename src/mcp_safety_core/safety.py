"""Tool-level safety helpers: read-only allowlisting and tool annotations.

These are deliberately *generic* and duck-typed against FastMCP-style server
objects (standalone ``fastmcp`` or ``mcp.server.fastmcp``). The exact mechanism
for stripping tools differs across FastMCP versions, so :func:`apply_name_allowlist`
works against a tool store that exposes ``list_tools()`` + ``remove_tool(name)``
and raises a clear error if none is found — a consumer adapts for its version.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

MUTATES_TAG = "mutating"
READ_ONLY_HINT = "readOnlyHint"
DESTRUCTIVE_HINT = "destructiveHint"

F = TypeVar("F", bound=Callable[..., Any])


def mark_mutating(fn: F, action: str | None = None) -> F:
    """Tag a function as a mutating tool so read-only filtering can skip it."""
    fn.__mutates__ = True  # type: ignore[attr-defined]
    if action is not None:
        fn.__action__ = action  # type: ignore[attr-defined]
    return fn


def is_mutating(fn: Any) -> bool:
    """Return True if the callable has been tagged ``__mutates__``."""
    return bool(getattr(fn, "__mutates__", False))


def tool_annotations(*, read_only: bool = False, destructive: bool = True) -> dict[str, bool]:
    """Return MCP tool-annotation hints (spec 2025-06-18 / SEP-2061)."""
    out: dict[str, bool] = {}
    if read_only:
        out[READ_ONLY_HINT] = True
    if destructive:
        out[DESTRUCTIVE_HINT] = True
    return out


class ToolStore:
    """Minimal tool-store contract used by :func:`apply_name_allowlist`.

    FastMCP generally provides an equivalent object (``local_provider`` /
    ``_tool_manager``) with ``remove_tool(name)``; adapters wrap whichever
    surface the installed FastMCP version exposes into this shape.
    """

    def __init__(self, names: list[str]) -> None:
        self._names = list(names)

    def list_tools(self) -> list[str]:
        return list(self._names)

    def remove_tool(self, name: str) -> None:
        try:
            self._names.remove(name)
        except ValueError:
            raise KeyError(name) from None


def apply_name_allowlist(
    store: ToolStore,
    allowed: Iterable[str] | None = None,
    *,
    is_mutating_tool: Callable[[str], bool] | None = None,
) -> int:
    """Drop tools from a :class:`ToolStore` when in read-only mode.

    Exactly one of ``allowed`` (the exact set of names to KEEP) or
    ``is_mutating_tool`` (predicate over a tool name) should be supplied;
    ``allowed`` takes precedence. Returns the number of tools removed.
    """
    names = store.list_tools()

    if allowed is not None:
        keep = set(allowed)
    elif is_mutating_tool is not None:
        keep = {n for n in names if not is_mutating_tool(n)}
    else:
        # Nothing to filter by; a no-op is safer than dropping everything.
        return 0

    removed = 0
    for name in names:
        if name not in keep:
            try:
                store.remove_tool(name)
                removed += 1
            except KeyError:
                pass
    return removed
