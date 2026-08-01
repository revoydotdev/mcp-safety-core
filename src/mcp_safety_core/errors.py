"""Structured (SERF-aligned) error envelope shared across the portfolio.

Implements the "Structured Error Recovery Framework" recommendation from
Srinivasan, *Missing MCP Primitives* (2026): machine-readable error codes plus
``retryable`` and ``suggested_action`` so an agent can branch deterministically
instead of hallucinating a recovery.

Each consumer keeps its own domain-specific StrEnum of codes and passes the
``code`` + extras; this module provides the shared base ``ErrorCode`` for common
fallbacks and the ``failure_response()`` envelope builder.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Common failure codes usable by any server."""

    BAD_REQUEST = "BAD_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    READ_ONLY = "READ_ONLY"
    INTERRUPTED = "INTERRUPTED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


# Default remediation text per code, so failure_response() can supply a useful
# next step even when the caller passes none.
_DEFAULT_REMEDIATION: dict[ErrorCode, str] = {
    ErrorCode.BAD_REQUEST: "Fix the request parameters and retry.",
    ErrorCode.NOT_FOUND: "The requested resource/entity does not exist.",
    ErrorCode.TOOL_NOT_FOUND: "The requested tool is not registered in this server.",
    ErrorCode.TIMEOUT: "The operation timed out; retry with a longer timeout.",
    ErrorCode.FAILED: "The operation failed; check the error_detail for cause.",
    ErrorCode.UNAVAILABLE: "A required dependency/backend is unavailable; start it and retry.",
    ErrorCode.NOT_CONFIGURED: "Configure the required creds/settings before use.",
    ErrorCode.READ_ONLY: "Refusing a mutating action in read-only mode.",
    ErrorCode.INTERRUPTED: "The operation was interrupted; state may need recovery.",
    ErrorCode.CANCELLED: "The operation was cancelled.",
    ErrorCode.UNKNOWN: "An unexpected error occurred; check the server logs.",
}


def failure_response(
    code: ErrorCode | str,
    detail: str = "",
    *,
    retryable: bool = False,
    suggested_action: str | None = None,
    **extras: Any,
) -> dict[str, Any]:
    """Build the uniform ``{ok: False, ...}`` error envelope.

    ``code`` may be a domain ``StrEnum`` member or any string; the common
    defaults in :data:`ErrorCode` are used for remediation when none is given.
    Extra keyword arguments are merged in (e.g. ``status_code``).
    """
    ecode = ErrorCode(code) if isinstance(code, str) and code in ErrorCode.__members__ else code
    remediation = suggested_action
    if remediation is None and isinstance(ecode, ErrorCode):
        remediation = _DEFAULT_REMEDIATION.get(ecode)
    return {
        "ok": False,
        "error_code": str(ecode.value) if isinstance(ecode, ErrorCode) else str(ecode),
        "error_detail": detail,
        "retryable": retryable,
        "suggested_action": remediation,
        **extras,
    }
