"""Tests for read-only filtering and tool annotations."""

from __future__ import annotations

from mcp_safety_core.safety import (
    DESTRUCTIVE_HINT,
    READ_ONLY_HINT,
    ToolStore,
    apply_name_allowlist,
    is_mutating,
    mark_mutating,
    tool_annotations,
)


def _store(*names: str) -> ToolStore:
    return ToolStore(list(names))


def test_mark_and_is_mutating() -> None:
    def f() -> None:  # pragma: no cover
        pass

    assert is_mutating(f) is False
    mark_mutating(f, action="wipe")
    assert is_mutating(f) is True
    assert f.__action__ == "wipe"  # type: ignore[attr-defined]


def test_tool_annotations_combinations() -> None:
    assert tool_annotations() == {DESTRUCTIVE_HINT: True}
    assert tool_annotations(read_only=True, destructive=False) == {READ_ONLY_HINT: True}
    both = tool_annotations(read_only=True, destructive=True)
    assert both == {READ_ONLY_HINT: True, DESTRUCTIVE_HINT: True}


def test_allowlist_keeps_only_listed() -> None:
    store = _store("a", "b", "c")
    removed = apply_name_allowlist(store, allowed=["a", "c"])
    assert removed == 1
    assert store.list_tools() == ["a", "c"]


def test_mutating_predicate_drops_destructive() -> None:
    store = _store("status", "wipe", "list")
    removed = apply_name_allowlist(store, is_mutating_tool=lambda n: n == "wipe")
    assert removed == 1
    assert store.list_tools() == ["status", "list"]


def test_noop_filter_returns_zero() -> None:
    store = _store("a", "b")
    assert apply_name_allowlist(store) == 0
    assert store.list_tools() == ["a", "b"]


def test_remove_missing_is_ignored() -> None:
    store = _store("a")
    removed = apply_name_allowlist(store, allowed=[])
    assert removed == 1
    assert store.list_tools() == []
