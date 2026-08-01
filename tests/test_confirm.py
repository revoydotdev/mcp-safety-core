"""Test suite for :mod:`mcp_safety_core.confirm`.

Covers the TDD contract from the remediation plan: Preview on ``confirm=False``,
execution on ``confirm=True``, target resolution, the optional ``describe``
summariser, and the return-type widening that lets an MCP server's output-schema
validation accept both ``T`` and ``Preview``.
"""

from __future__ import annotations

from typing import Any, TypeVar, get_type_hints

from mcp_safety_core.confirm import Preview, confirm_required

T = TypeVar("T")


def test_confirm_false_returns_preview_not_execute() -> None:
    calls: list[dict[str, Any]] = []

    @confirm_required("install for")
    def do_install(game_id: int, confirm: bool = False) -> dict[str, Any]:
        calls.append({"game_id": game_id})
        return {"ok": True}

    result = do_install(game_id=42)
    assert isinstance(result, Preview)
    assert result.preview is True
    assert result.target == "42"
    assert "install for" in result.would_do
    assert result.note == "Pass confirm=True to execute."
    assert calls == []  # the wrapped function must NOT have run


def test_confirm_true_executes() -> None:
    calls: list[dict[str, Any]] = []

    @confirm_required("install")
    def do_install(game_id: int, confirm: bool = False) -> dict[str, Any]:
        calls.append({"game_id": game_id})
        return {"ok": True, "launched": True}

    result = do_install(game_id=42, confirm=True)
    assert result == {"ok": True, "launched": True}
    assert calls == [{"game_id": 42}]


def test_target_resolution_prefers_first_nonempty_target_param() -> None:
    @confirm_required("action")
    def op(slug: str | None = None, game_id: str = "") -> dict[str, Any]:
        return {"ok": True}

    result = op(slug=None, game_id="abc123")
    assert isinstance(result, Preview)
    assert result.target == "abc123"


def test_target_truncated_to_160_chars() -> None:
    @confirm_required("action")
    def op(path: str = "x") -> dict[str, Any]:
        return {"ok": True}

    long = "p" * 300
    result = op(path=long)
    assert isinstance(result, Preview)
    assert len(result.target) == 160


def test_unknown_target_falls_back() -> None:
    @confirm_required("action")
    def op(some_arg: int) -> dict[str, Any]:
        return {"ok": True}

    result = op(some_arg=7)
    assert isinstance(result, Preview)
    assert result.target == "<unknown>"


def test_describe_summariser_overrides_would_do() -> None:
    def describe(args: dict[str, Any]) -> str | None:
        return f"install {args['name']} with runner {args['runner']}"

    @confirm_required("install", describe=describe)
    def op(name: str, runner: str, confirm: bool = False) -> dict[str, Any]:
        return {"ok": True}

    result = op(name="portal2", runner="wine", confirm=False)
    assert isinstance(result, Preview)
    assert result.would_do == "install portal2 with runner wine"


def test_describe_exception_falls_back_to_generic() -> None:
    def describe(args: dict[str, Any]) -> str:
        raise RuntimeError("boom")

    @confirm_required("install", describe=describe)
    def op(game_id: int, confirm: bool = False) -> dict[str, Any]:
        return {"ok": True}

    result = op(game_id=5)
    assert isinstance(result, Preview)
    assert "install on 5" in result.would_do


def test_return_annotation_widened_to_include_preview() -> None:
    """The widen must be visible to MCP output-schema validation."""

    @confirm_required("install")
    def op(game_id: int, confirm: bool = False) -> dict[str, Any]:
        return {"ok": True}

    ret = get_type_hints(op).get("return")
    assert ret is not None
    # `dict[str, Any] | Preview` — Preview must be a member of the union
    assert "Preview" in str(ret)


def test_mutates_and_action_markers_set() -> None:
    @confirm_required("wipe")
    def op(confirm: bool = False) -> dict[str, Any]:
        return {"ok": True}

    assert op.__mutates__ is True  # type: ignore[attr-defined]
    assert op.__action__ == "wipe"  # type: ignore[attr-defined]


def test_confirm_accepts_custom_target_params() -> None:
    @confirm_required("scan", target_params=("ips", "alert_id", "out_dir"))
    def op(ips: str = "", alert_id: str = "", confirm: bool = False) -> dict[str, Any]:
        return {"ok": True}

    # "ips" is not in the default param list; without target_params this would be <unknown>
    preview = op(ips="1.2.3.4")
    assert isinstance(preview, Preview)
    assert preview.target == "1.2.3.4"

    preview2 = op(ips="", alert_id="alert-99")
    assert isinstance(preview2, Preview)
    assert preview2.target == "alert-99"
