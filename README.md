<div align="center">

# mcp-safety-core

### Small, explicit safety primitives for Python MCP tools

**Preview mutations. Structure failures. Keep read-only mode honest.**

[![CI](https://github.com/revoydotdev/mcp-safety-core/actions/workflows/ci.yml/badge.svg)](https://github.com/revoydotdev/mcp-safety-core/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-526b4e.svg)](LICENSE)

[Install](#requirements-and-installation) · [Confirm gate](#preview-then-confirm) · [Errors](#structured-errors) · [Read-only tools](#read-only-toolsets-and-annotations) · [Development](#development)

</div>

`mcp-safety-core` gives
tool authors three composable building blocks: a preview-before-execution
confirm gate, a consistent structured-error envelope, and helpers for marking
or filtering mutating tools.

It is deliberately framework-light. The core dependency is
[Pydantic](https://docs.pydantic.dev/) and optional extras support projects that
also use the MCP SDK or FastMCP.

## What it provides

| Need | Primitive | Result |
| --- | --- | --- |
| Let a caller inspect a mutating action before it runs | `@confirm_required(...)` | A typed `Preview` until `confirm=True` is supplied |
| Give an agent a predictable failure shape | `failure_response(...)` | A `{ok: False, error_code, error_detail, retryable, suggested_action}` mapping |
| Identify or omit mutating tools in read-only mode | `mark_mutating`, `is_mutating`, `apply_name_allowlist` | Explicit tool metadata and name-based filtering |
| Supply MCP annotation hints | `tool_annotations(...)` | `readOnlyHint` and/or `destructiveHint` mappings |

The package supplies library primitives; it does not register tools, enforce
authentication, or run an MCP server for you. Apply the gate at the callable
that performs the mutation, and keep authorization and server policy in the
hosting application.

## Requirements and installation

Python 3.11 or newer is required. The core package depends only on
`pydantic>=2.6`.

```bash
uv add "mcp-safety-core @ git+https://github.com/revoydotdev/mcp-safety-core.git"
uv add "mcp-safety-core[mcp] @ git+https://github.com/revoydotdev/mcp-safety-core.git"
uv add "mcp-safety-core[fastmcp] @ git+https://github.com/revoydotdev/mcp-safety-core.git"
```

The package is currently installed from the public source repository; it is
not published on PyPI yet. Pin a tag or commit in production environments.

## Preview, then confirm

Decorate a mutating callable that accepts a `confirm: bool = False` parameter.
When confirmation is absent or false, the decorated function is not called;
the decorator returns a `Preview`. On `confirm=True`, it calls the original
function. The wrapper's return annotation includes both the function's declared
return type and `Preview`.

```python
from mcp_safety_core import Preview, confirm_required


@confirm_required("cancel job")
def cancel_job(job_id: str, confirm: bool = False) -> dict[str, object]:
    # Perform the actual mutation here.
    return {"ok": True, "cancelled": job_id}


preview = cancel_job("job-42")
assert isinstance(preview, Preview)
assert preview.model_dump() == {
    "preview": True,
    "action": "cancel job",
    "target": "job-42",
    "would_do": "cancel job on job-42",
    "note": "Pass confirm=True to execute.",
}

result = cancel_job("job-42", confirm=True)
assert result == {"ok": True, "cancelled": "job-42"}
```

`confirm_required` has this signature:

```python
confirm_required(action, describe=None, *, target_params=(...))
```

`target_params` controls which bound arguments are used, in order, for the
preview target. Its default recognizes common names such as `slug`, `game_id`,
`path`, `query`, `job_id`, and `name`; pass domain-specific names when needed.
`describe` receives the bound arguments as a dictionary and can return a more
specific `would_do` message. If it raises or returns a falsey value, the
generic action-and-target description is used instead.

```python
from typing import Any

from mcp_safety_core.confirm import confirm_required


def describe_scan(args: dict[str, Any]) -> str:
    return f"scan {args['ips']} and write findings to {args['out_dir']}"


@confirm_required(
    "scan",
    describe=describe_scan,
    target_params=("ips", "alert_id", "out_dir"),
)
def scan(ips: str, out_dir: str, confirm: bool = False) -> dict[str, bool]:
    return {"ok": True}
```

The decorator also sets `__mutates__ = True` and `__action__` on its wrapper,
so the same callable can participate in read-only filtering.

## Structured errors

`failure_response` builds an ordinary dictionary for predictable tool errors.
Use an `ErrorCode` member for common failures, or provide a string or a
domain-specific `StrEnum` member. Common `ErrorCode` values receive a default
suggested action when one is not supplied; domain-specific codes do not.

```python
from mcp_safety_core import ErrorCode, failure_response


response = failure_response(
    ErrorCode.READ_ONLY,
    "Deleting a job is disabled in read-only mode.",
    status_code=403,
)

assert response == {
    "ok": False,
    "error_code": "READ_ONLY",
    "error_detail": "Deleting a job is disabled in read-only mode.",
    "retryable": False,
    "suggested_action": "Refusing a mutating action in read-only mode.",
    "status_code": 403,
}
```

The shared `ErrorCode` enum contains `BAD_REQUEST`, `NOT_FOUND`,
`TOOL_NOT_FOUND`, `TIMEOUT`, `FAILED`, `UNAVAILABLE`, `NOT_CONFIGURED`,
`READ_ONLY`, `INTERRUPTED`, `CANCELLED`, and `UNKNOWN`.

## Read-only toolsets and annotations

Use `mark_mutating` for a callable that should be labelled mutating but does
not need a confirmation preview. `is_mutating` reads that marker.

```python
from mcp_safety_core.safety import is_mutating, mark_mutating, tool_annotations


@mark_mutating
def rebuild_index() -> None:
    pass


assert is_mutating(rebuild_index)
assert tool_annotations(read_only=True, destructive=False) == {"readOnlyHint": True}
```

`tool_annotations(read_only=False, destructive=True)` returns MCP-style hint
mappings. By default it returns `{"destructiveHint": True}`.

For a read-only server mode, `apply_name_allowlist` removes names from a tool
store. The included `ToolStore` is a small implementation of the required
`list_tools()` / `remove_tool(name)` interface; applications can adapt their
own store to that shape.

```python
from mcp_safety_core import apply_name_allowlist
from mcp_safety_core.safety import ToolStore


store = ToolStore(["status", "list_jobs", "delete_job"])
removed = apply_name_allowlist(store, allowed=["status", "list_jobs"])

assert removed == 1
assert store.list_tools() == ["status", "list_jobs"]
```

Alternatively, pass `is_mutating_tool` to remove every name for which the
predicate returns true. If neither `allowed` nor `is_mutating_tool` is given,
the function makes no changes. When both are provided, `allowed` takes
precedence.

## Public imports

The package root exports the most common primitives:

```python
from mcp_safety_core import (
    ErrorCode,
    Preview,
    apply_name_allowlist,
    confirm_required,
    failure_response,
)
```

Import `ToolStore`, `mark_mutating`, `is_mutating`, and `tool_annotations` from
`mcp_safety_core.safety`.

## Development

Set up the development extra, then run the repository checks:

```bash
uv sync --extra dev
uv run python -m ruff check .
uv run python -m ruff format --check .
uv run python -m mypy src
uv run python -m pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution expectations and
[GUIDELINES.md](GUIDELINES.md) for the project's testing and quality standards.

## License

[MIT](LICENSE) © 2026 revelri
