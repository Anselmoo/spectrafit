---
title: "CLI Typer/Rich UX Modernization"
category: "Architecture"
status: "🔴 Not Started"
priority: "High"
timebox: "1 week"
created: 2026-03-07
updated: 2026-03-07
owner: ""
tags: ["technical-spike", "cli", "typer", "rich", "ux", "architecture"]
---

# CLI Typer/Rich UX Modernization

## Summary

**Spike Objective:** Audit the entire `spectrafit/cli/` surface, identify all UX gaps (missing
color, empty stubs, legacy patterns, broken flows), and produce a concrete implementation plan
that brings the CLI to state-of-the-art Typer ≥ 0.20 + Rich 14 standards.

**Why This Matters:** The core fitting pipeline (`uv run spectrafit fit examples/basic/input.toml`)
runs correctly, but the CLI presents a degraded experience: no progress feedback during fitting,
inconsistent colour output, empty stub methods in `PrintingStatus`, a duplicate
`__status__.start()` call, and `rich` markup disabled app-wide.  For a scientific tool where
users wait for iterative fits, the feedback gap erodes trust and usability.

**Timebox:** 1 week

**Decision Deadline:** Before Phase 6 (frozen modules are thawed); CLI UX work should be
complete before `postprocessing.py` / `printer.py` are refactored.

---

## Research Question(s)

**Primary Question:** What is the minimal, correct set of changes required to give SpectraFit's
CLI state-of-the-art Typer + Rich UX — consistent colour, progress feedback, and a clean API
surface — without touching frozen modules?

**Secondary Questions:**

1. Should `rich` be declared as a **direct** dependency (in `pyproject.toml`) or is `typer[all]`
   the right vehicle?
2. What is the idiomatic pattern in Typer 0.20+ for a **Rich progress spinner** around a
   long-running synchronous call (`fitting_routine_pipeline`)?
3. Should `rich_markup_mode` be `"rich"` (full markup) or `"markdown"` for help strings?
4. What should replace the empty `PrintingStatus.start()` / `end()` stubs — a `rich.status`
   context manager, a `rich.progress` bar, or a simple spinner?
5. Are there additional CLI gaps (bad flag names, inconsistent error handling, missing exit codes,
   missing command features) that should be tracked as separate issues vs. fixed in this spike?

---

## Current State Audit

### Confirmed Bugs

| Location | Issue | Severity |
|----------|-------|----------|
| `cli/commands/fit.py:67,70` | `__status__.start()` called twice (once before loop, once inside) | Medium |
| `cli/commands/fit.py:69` | Infinite `while True:` loop — `noplot=True` exits but logic is fragile | Low |

### Missing Features / UX Gaps

| Location | Gap | Notes |
|----------|-----|-------|
| `cli/main.py` | `rich_markup_mode` not set on `typer.Typer(...)` | Rich markup disabled in all help text |
| `cli/main.py` | No `pretty_exceptions_enable=True` or `pretty_exceptions_show_locals` | Typer ≥ 0.9 supports Rich pretty exceptions |
| `cli/commands/fit.py` | No spinner/progress during `fitting_routine_pipeline()` | User sees blank terminal while fitting runs |
| `cli/commands/fit.py` | `--verbose/-vb` uses non-standard short flag (`-vb`) | Convention is `-v` / `--verbose`; `-v` is taken by `--version` at root level only |
| `cli/commands/fit.py` | `__status__.start()` / `.end()` are no-ops; never show anything | Dead code leaking from legacy API |
| `cli/commands/convert.py` | Error messages lack `typer.style(…, fg=typer.colors.RED)` | Plain `❌` prefix only, no color |
| `cli/commands/report.py` | Error messages lack `typer.style()` | Same as convert |
| `cli/commands/scaffolding.py` | `init` success output lacks green styling | Inconsistent with `validate` |
| `report/printer.py` | `PrintingStatus.start()` / `end()` / `welcome()` / `credits()` / `yes_no()` are stubs | Legacy shapes that need implementing or removing |
| `report/printer.py` | `print_tabulate_df()` is explicitly a no-op placeholder | Comment says "intentionally empty" |
| `pyproject.toml` | `typer>=0.20.0` (bare) instead of `typer[all]` | `rich` is a transitive dep, not guaranteed |

### Legacy Patterns

| Pattern | Where | Recommended Replacement |
|---------|-------|------------------------|
| `art.tprint()` in `PrintingStatus.welcome()` | `report/printer.py` | `rich.panel.Panel` / `rich.text.Text` |
| `pprint.PrettyPrinter` for verbose output | `report/printer.py` | `rich.pretty.pprint` |
| Bare `typer.echo()` (no style) for status | Multiple commands | `typer.echo(typer.style(…))` or `rich.console.Console().print(…)` |

### `rich` Dependency Status

`rich 14.3.3` is present in `uv.lock` as a **transitive** dependency (pulled in by something
else, e.g. `tqdm`, `dtale`, or another dep). It is **not** declared in `pyproject.toml`
`[project.dependencies]`, so it could disappear if that upstream dep is removed. The correct
fix is to either:

- Add `"rich>=14.0"` explicitly, **or**
- Upgrade to `"typer[all]>=0.20.0"` (which pins `rich` as a direct typer extra)

---

## Investigation Plan

### Research Tasks

- [ ] Read Typer 0.20–0.24 changelog for `rich_markup_mode`, pretty exceptions, and
      `typer.Typer(callback=…)` patterns
- [ ] Read Rich 14 docs for `Console`, `Progress`, `Status` (spinner), `Panel`, and `Table`
      patterns suitable for CLI output
- [ ] Survey reference projects (pyglotaran, lmfit CLI, typical scientific Python CLIs) for
      state-of-the-art patterns
- [ ] Prototype a spinner around `fitting_routine_pipeline()` using `with Progress(…):` or
      `with Status(…):` and verify it works under CI (non-TTY) conditions
- [ ] Determine the correct approach for the `--verbose / -vb` flag conflict (root `-v` for
      version vs sub-command `-v` for verbose)
- [ ] Decide: replace `PrintingStatus` stubs in-place, or introduce a new
      `spectrafit/cli/_console.py` singleton?
- [ ] Document findings and produce a ranked list of implementation tasks

### Success Criteria

**This spike is complete when:**

- [ ] A concrete decision is documented: `typer[all]` vs `rich` direct dep
- [ ] The `rich_markup_mode` value is chosen and justified
- [ ] A spinner/progress pattern for the `fit` command is prototyped and verified
- [ ] All gaps in the audit table above are triaged (fix now / defer / won't fix)
- [ ] An ordered implementation plan is captured in the Follow-up Actions section

---

## Technical Context

**Related Components:**

- `spectrafit/cli/` — all files (main, commands/*)
- `spectrafit/report/printer.py` — `PrintingStatus` (FROZEN until Phase 6)
- `pyproject.toml` — dependency declarations
- `tests/` — integration tests for CLI commands

**Dependencies:**

- This spike must be resolved before refactoring `report/printer.py` (Phase 6+)
- `PrintingStatus.start()` / `end()` stubs are **frozen** until Phase 6 — the spike should
  clarify whether the UX fix requires Phase 6 or can be done purely in `spectrafit/cli/`
- The `fit` command duplicate-start bug can be fixed immediately (not frozen)

**Constraints:**

- `spectrafit/core/preprocessing.py`, `postprocessing.py`, `plugins/` are frozen until Phase 6
- `printer.py` is frozen — new Rich code must live in `spectrafit/cli/` for now
- `typer >= 0.20.0` is the minimum supported version; must not use features exclusive to
  later releases without bumping the constraint
- Python 3.10 minimum — no walrus assignments in type annotations

---

## Research Findings

### Confirmed: `rich_markup_mode` missing

`typer.Typer(rich_markup_mode=None)` (the default) silently strips all Rich markup from
help text. Setting `rich_markup_mode="rich"` enables `[bold]`, `[green]`, `[link …]` etc.
in docstrings. Setting it to `"markdown"` enables `**bold**`, `*italic*` syntax instead.
For SpectraFit, `"rich"` is recommended (matches how `validate` / `fit` use `typer.style()`).

### Confirmed: Double `__status__.start()` bug

```python
# fit.py:67 — before the loop (dead, immediately re-called)
__status__.start()

while True:
    __status__.start()  # ← only this one matters; the outer call is unreachable noise
```

Fix: remove line 67.

### Confirmed: `typer[all]` recommended

Typer's extras split is:
- `typer` (bare) — includes `click`; `rich` is optional
- `typer[all]` — adds `rich` and `shellingham`

Using `typer[all]` is the canonical way to ensure Rich is available for help rendering,
pretty exceptions, and `typer.style()`.

---

## Decision

### Recommendation

*(To be filled after investigation — template for expected outcome)*

**Phase A — Immediate bug fixes (no frozen code touched):**

1. Remove duplicate `__status__.start()` at `fit.py:67`
2. Change `pyproject.toml`: `"typer>=0.20.0"` → `"typer[all]>=0.20.0"`
3. Add `rich_markup_mode="rich"` and `pretty_exceptions_enable=True` to `typer.Typer(…)` in
   `cli/main.py`
4. Add `typer.style()` to bare `typer.echo()` calls in `convert.py`, `report.py`,
   `scaffolding.py`
5. Add a `rich.status.Status` spinner in `fit.py` around `fitting_routine_pipeline()` call

**Phase B — Stub cleanup (requires Phase 6 / printer.py unfreeze):**

6. Implement or remove `PrintingStatus.start()` / `end()` / `welcome()` using Rich
7. Replace `art.tprint()` in `PrintingStatus.welcome()` with `rich.panel.Panel` header
8. Replace `pprint.PrettyPrinter` with `rich.pretty.pprint`
9. Implement `print_tabulate_df()` (currently a documented no-op placeholder)

**Phase C — UX polish (evaluate scope):**

10. Evaluate rename of `-np/--noplot` → `--no-plot` (breaking change, needs major bump)
11. Evaluate a `spectrafit/cli/_console.py` `Console` singleton for consistent output
12. Evaluate Rich `Table` for fit results output replacing plain-text tabulate

### Rationale

*(To be filled after prototyping)*

### Implementation Notes

- Spinner must degrade gracefully when `stdout` is not a TTY (CI logs, piped output).
  Use `transient=True` on `rich.status.Status` so it clears after fitting.
- `typer[all]` pulls in `shellingham` for shell completion detection — verify that
  `add_completion=False` in `cli/main.py` still suppresses completion install prompts.
- Frozen modules: `printer.py` changes go in a separate PR gated on Phase 6 start.

### Follow-up Actions

- [ ] Fix: remove duplicate `__status__.start()` in `fit.py:67`
- [ ] Fix: `pyproject.toml` → `typer[all]>=0.20.0`
- [ ] Fix: add `rich_markup_mode="rich"`, `pretty_exceptions_enable=True` to app
- [ ] Fix: consistent `typer.style()` across `convert.py`, `report.py`, `scaffolding.py`
- [ ] Feat: Rich spinner/progress in `fit.py` around pipeline call
- [ ] Feat (Phase 6): implement `PrintingStatus.start()` / `end()` with `rich.status`
- [ ] Chore: evaluate whether `art` dep (`art.tprint`) can be removed if `rich` replaces welcome
- [ ] Create GitHub issues for Phase A items (immediate, no freeze risk)
- [ ] Update `architecture.instructions.md` with CLI UX conventions

---

## Status History

| Date       | Status         | Notes                                                      |
|------------|----------------|------------------------------------------------------------|
| 2026-03-07 | 🔴 Not Started | Spike created; full CLI audit completed; Phase A items identified |

---

_Last updated: 2026-03-07_
