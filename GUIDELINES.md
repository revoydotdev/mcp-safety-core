# GUIDELINES.md — Program standards for mcp-safety-core

These are the TDD and syntax standards the whole revelri MCP portfolio follows.
This library is the first project to codify and enforce them.

## TDD (test-first, evidence over assertion)

1. **Red → Green → Refactor, per todo.** Every change that adds or alters
   behavior starts with a **failing test** (or a stubbed failing test) committed
   first, then the implementation, then a refactor pass. A todo with no test is
   not done.
2. **Coverage floor: 80%** for this package (`--cov-fail-under=80`), enforced in
   CI. Protect the safety-critical paths (confirm gate, bearer isolation,
   error envelope) with dedicated tests even if the aggregate floor is met.
3. **Test markers:** use a `live` marker for anything needing real external
   state (network, a running service). CI runs only non-live tests; live tests
   run in a scheduled/live matrix and never block PR CI.
4. **Pure functions first:** unit-test the pure helpers (`_resolve_target`,
   `failure_response`, `apply_name_allowlist`, `shape_to_schema`-style mappers)
   before any integration test — they are the cheapest highest-value coverage.
5. **Regression fixtures:** any bug fixed adds a failing test fixture first, so
   the exact failure case is locked before the fix.

## Syntax & tooling

- **Lint:** `ruff check` (rules: E, F, I, UP, B, SIM, N, ARG).
- **Format:** `ruff format --check` (line length 100).
- **Types:** `mypy --strict`, `warn_unused_ignores = True`. No `type: ignore`
  without a comment; no `as Any` on public signatures.
- **Build:** `uv` + `hatchling`, `requires-python >= 3.11`, committed `uv.lock`.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`,
  `docs:`, `chore:`, `perf:`, `build:`). Each todo = exactly one commit on the
  worktree branch. No wip/tmp/"fix fix fix".
- **Behavior changes require an ADR** appended under `decisions/`.
- **CI gates:** ruff → ruff format → mypy --strict → pytest + coverage floor →
  (for servers) schema-snapshot diff and smoke boot.

## Definition of done (per phase)

- Every todo committed with its test; test-first ordering visible in `git log`.
- `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` all green.
- Coverage floor not lowered.
- Docs (README/CHANGELOG/ADRs) kept true to the code.
- Disjoint-ownership holds: no LANE of the portfolio edits another lane's repo.
