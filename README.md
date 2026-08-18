# mcp-safety-core

Single-source safety primitives shared across the revelri MCP portfolio:
preview→confirm gating for destructive tools, a SERF-aligned structured-error
envelope, and tool-safety helpers (read-only filtering + annotations).

This library exists to **deduplicate** a pattern that was independently
copied into four sibling MCP servers (`lutris-mcp`, `nicotine-mcp`,
`shodan-mcp`, `apk-lab-mcp`). `shodan-mcp` and `apk-lab-mcp` have migrated to
depend on the published package rather than shipping their own copy;
`lutris-mcp` and `nicotine-mcp` still carry their original local copies
pending migration.

## Install

```bash
uv add mcp-safety-core            # core primitives (pydantic only)
uv add "mcp-safety-core[mcp]"     # + mcp SDK
uv add "mcp-safety-core[fastmcp]" # + fastmcp
```

## Modules

| Module | Purpose |
|---|---|
| `mcp_safety_core.confirm` | `@confirm_required("action")` — returns a `Preview` on `confirm=False`, executes on `confirm=True`; widens the return annotation to `T \| Preview` so MCP output-schema validation accepts both. Sets `__mutates__`/`__action__` for read-only filtering. |
| `mcp_safety_core.errors` | `ErrorCode` (common fallbacks) + `failure_response(code, detail, retryable, suggested_action, **extras)` → `{ok: False, error_code, error_detail, retryable, suggested_action, ...}`. SERF-aligned so agents branch deterministically. |
| `mcp_safety_core.safety` | `mark_mutating`/`is_mutating`, `tool_annotations(read_only, destructive)` (SEP-2061 hints), and `apply_name_allowlist(store, allowed|is_mutating_tool)` for read-only tool stripping via a `ToolStore`. |

## Quick example

```python
from mcp_safety_core.confirm import confirm_required, Preview


@confirm_required("factory-reset", name="dummy")
def waydroid_init(serial: str, confirm: bool = False) -> dict:
    """Wipe a container. Returns Preview unless confirm=True."""
    return {"ok": True, "wiped": serial}


# Calling without confirm=True is a no-op that returns a description:
result = waydroid_init(serial="emulator-5554")  # -> Preview, server not touched
```

## Development

See [GUIDELINES.md](GUIDELINES.md) (TDD + syntax standards) and
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — Copyright (c) 2026 revelri
