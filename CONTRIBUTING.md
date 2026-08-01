# CONTRIBUTING.md

## Getting started

```bash
uv sync --extra dev
uv run pytest
```

## Before opening a change

1. Write/run a failing test first (TDD — see GUIDELINES.md).
2. Implement; keep the diff atomic and one commit per concern.
3. Run the full gate:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src
   uv run pytest
   ```
4. Use Conventional Commits. If the change alters behavior or the public API,
   add an ADR under `decisions/`.

## Rules

- Never lower the coverage floor.
- Never add `type: ignore` / `as Any` to escape typing.
- Never edit a consumer's repository from this one — this is the shared library;
  consumers consume a published version, they do not edit the source.
