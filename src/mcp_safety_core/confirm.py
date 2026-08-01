"""Confirm-gate decorator for destructive tools.

A faithful, deduplicated port of the pattern originally implemented in
``lutris-mcp/lutris_mcp/confirm.py`` (and mirrored in ``nicotine-mcp`` /
``shodan-mcp`` / ``apk-lab-mcp``). This library is the single source so those
repos can drop their local copies.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, get_type_hints

from pydantic import BaseModel

F = TypeVar("F", bound=Callable[..., Any])

# Parameter names checked (in order) to summarize the target of a previewed
# action. First non-empty string wins; falls back to "<unknown>". Consumers with
# domain-specific params (e.g. shodan's ``ips``/``alert_id``, apk-lab's
# ``serial``) pass an explicit ``target_params=`` tuple to :func:`confirm_required`.
_DEFAULT_TARGET_PARAMS = (
    "slug",
    "game_id",
    "path",
    "query",
    "infohash",
    "job_id",
    "name",
    "service",
    "username",
    "category",
    "yaml_text",
)

_TARGET_MAX = 160


class Preview(BaseModel):
    """Structured description of an action that will run on confirm=True."""

    preview: bool = True
    action: str
    target: str
    would_do: str
    note: str = "Pass confirm=True to execute."


def _resolve_target(bound: inspect.BoundArguments, target_params: tuple[str, ...]) -> str:
    for key in target_params:
        if key in bound.arguments:
            value = bound.arguments[key]
            if value is None:
                continue
            text = str(value)
            if not text:
                continue
            return text[:_TARGET_MAX]
    return "<unknown>"


def confirm_required(
    action: str,
    describe: Callable[[dict[str, Any]], str | None] | None = None,
    *,
    target_params: tuple[str, ...] = _DEFAULT_TARGET_PARAMS,
) -> Callable[[F], F]:
    """Gate a mutating tool behind ``confirm=True``.

    ``describe`` is an optional summariser: given the tool's bound arguments
    (a plain ``name -> value`` dict), it returns a human-readable one-liner
    used as the preview's ``would_do`` so the agent can show the caller what
    the action will actually do. Best-effort: any exception falls back to the
    generic ``<action> on <target>`` text.

    ``target_params`` selects which bound arguments (in order) summarize the
    preview ``target``; pass the consumer's domain-specific names (e.g. shodan's
    ``("query", "ips", "alert_id")``) so deduplicated copies resolve the same
    target they did before.
    """

    def decorator(fn: F) -> F:
        sig = inspect.signature(fn)

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                bound = sig.bind_partial(*args, **kwargs)
            except TypeError:
                # Let the wrapped function surface the real signature error.
                return fn(*args, **kwargs)
            bound.apply_defaults()
            if not bool(bound.arguments.get("confirm", False)):
                target = _resolve_target(bound, target_params)
                would_do = f"{action} on {target}"
                if describe is not None:
                    try:
                        summary = describe(dict(bound.arguments))
                    except Exception:
                        summary = None
                    if summary:
                        would_do = summary
                return Preview(action=action, target=target, would_do=would_do)
            return fn(*args, **kwargs)

        # The confirm=False branch returns a Preview, not the wrapped function's
        # declared return type. FastMCP derives a structured output schema from
        # the return annotation and validates every response against it, so a
        # typed return like ``-> RunResult`` would reject the Preview. Widen the
        # advertised return to ``Orig | Preview`` so both validate. Resolve the
        # hint to a real class first: callers use ``from __future__ import
        # annotations``, so the raw annotation is a string ForwardRef pydantic
        # cannot build a schema from.
        try:
            orig_ret = get_type_hints(fn).get("return", inspect.Signature.empty)
        except Exception:
            orig_ret = inspect.Signature.empty
        widened_ret = Preview if orig_ret is inspect.Signature.empty else orig_ret | Preview
        wrapper.__annotations__ = {**getattr(fn, "__annotations__", {}), "return": widened_ret}

        # Read by servers to skip registration in --read-only mode.
        wrapper.__mutates__ = True  # type: ignore[attr-defined]
        wrapper.__action__ = action  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    return decorator
