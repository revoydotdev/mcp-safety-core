"""mcp-safety-core — shared safety primitives for the revelri MCP portfolio.

Single source for:
- ``confirm``  — the preview->confirm two-phase gate for destructive tools,
- ``errors``   — the SERF-aligned structured-error envelope,
- ``safety``   — read-only filtering, toolset gating, and tool annotations.

Consumers depend on this package (a published version) rather than duplicating
the pattern. See GUIDELINES.md.
"""

from mcp_safety_core.confirm import Preview, confirm_required
from mcp_safety_core.errors import ErrorCode, failure_response
from mcp_safety_core.safety import apply_name_allowlist

__all__ = [
    "Preview",
    "confirm_required",
    "ErrorCode",
    "failure_response",
    "apply_name_allowlist",
]

__version__ = "0.1.0"
