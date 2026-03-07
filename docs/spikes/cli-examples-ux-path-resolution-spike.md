---
title: "CLI Examples UX — Path Resolution & Command Syntax"
category: "Architecture"
status: "🟢 Complete"
priority: "High"
timebox: "1 day"
created: 2026-03-07
updated: 2026-03-07
owner: "SpectraFit team"
tags: ["technical-spike", "architecture", "cli", "examples"]
---

# CLI Examples UX — Path Resolution & Command Syntax

## Summary

**Spike Objective:** Determine the correct v2 CLI invocation for the `examples/` directory
and decide how relative `infile` paths inside TOML config files should be resolved.

**Why This Matters:** The `examples/*/README.md` files document invalid commands that fail
immediately when tried by a new user.  This undermines the community's confidence in the
project and blocks adoption of the v2 schema.

**Timebox:** 1 day (investigation + fix)

**Decision Deadline:** Before v2.0.0 release

## Research Question(s)

**Primary Question:** Should `infile` in a TOML config be resolved relative to the
TOML file's parent directory (config-relative) or relative to the process working
directory (CWD-relative)?

**Secondary Questions:**

- What is the correct `spectrafit fit` CLI command for running an example?
- Should `poe generate-examples` be the canonical way to regenerate data?
- Does the fix to `from_file()` break any existing tests or integrations?

## Investigation Plan

### Research Tasks

- [x] Audit `examples/*/README.md` for broken commands
- [x] Trace `from_file()` → `DataConfig` → `load_data()` path resolution chain
- [x] Test `uv run spectrafit fit examples/basic/input.toml --noplot` from repo root
- [x] Check `pyproject.toml` for existing `poe generate-examples` task
- [x] Confirm fix scope (only `from_file`, not `FittingPipeline.run()`)

### Success Criteria

**This spike is complete when:**

- [x] Root cause identified: `from_file()` does not rebase relative `infile` to TOML dir
- [x] Correct CLI command documented
- [x] Fix location identified
- [x] All example READMEs show working commands

## Technical Context

**Related Components:**
- `spectrafit/core/fitting_config.py` — `UnifiedFittingConfig.from_file()`
- `spectrafit/cli/commands/fit.py` — `fit()` typer command
- `examples/*/input.toml` — `[data] infile = "data.csv"` (relative path)
- `examples/*/README.md` — user-facing documentation

**Dependencies:** None (self-contained fix)

**Constraints:**
- Must not break the integration tests in `tests/integration/test_examples.py`
  (they already patch `raw["data"]["infile"]` to an absolute path)
- Must not break v1 backward-compat path (`migrate_v1_format` uses a different code path)

## Research Findings

### Investigation Results

**Issue 1 — Wrong CLI syntax in READMEs**

The v1 CLI accepted `spectrafit <data.csv> -i <input.toml>`.
The v2 CLI is a Typer multi-command app:

```
spectrafit fit <config.toml>   # correct v2 syntax
```

The argument is the *config file*, not the data file.  The data file is specified
inside the TOML under `[data] infile = ...`.

**Issue 2 — CWD-relative `infile` breaks `spectrafit fit` from repo root**

`from_file(path)` in `fitting_config.py` (line 471) does:

```python
with path.open("rb") as fb:
    raw = tomli.load(fb)
return cls.model_validate(raw)
```

It never rebases `raw["data"]["infile"]` against `path.parent`.  When the user
runs `uv run spectrafit fit examples/basic/input.toml` from the repo root, the
pipeline tries to open `./data.csv` (CWD), not `./examples/basic/data.csv`.

**Fix:** after loading `raw`, if `raw.get("data", {}).get("infile")` is a relative
path, resolve it against `path.parent` before calling `model_validate`.

**Issue 3 — Inconsistent generate command**

`poe generate-examples` already exists in `pyproject.toml`.  READMEs should
reference it instead of `uv run python scripts/generate_examples.py`.

### Prototype/Testing Notes

```bash
# Before fix (fails):
uv run spectrafit fit examples/basic/input.toml --noplot
# → "Fitting error: [Errno 2] No such file or directory: 'data.csv'"

# After fix (expected to pass):
uv run spectrafit fit examples/basic/input.toml --noplot
# → table output, fit converges
```

### External Resources

- [lmfit docs — parameter constraints](https://lmfit.github.io/lmfit-py/constraints.html)
- [Typer docs — file arguments](https://typer.tiangolo.com/tutorial/arguments/file/)

## Decision

### Recommendation

**Resolve `infile` relative to the TOML file's parent directory** when the path is relative.
This is the universally expected behaviour for config files (e.g. `pyproject.toml`,
`mkdocs.yml`, `Cargo.toml` all follow config-relative resolution).

CWD-relative is fine only when the caller constructs a `DataConfig` directly (API usage).

### Rationale

- Users expect `spectrafit fit path/to/input.toml` to work regardless of CWD
- Config files in the wild always sit next to their data; config-relative is natural
- The fix is a 4-line patch in `from_file()` with zero downstream impact

### Implementation Notes

In `UnifiedFittingConfig.from_file()`, after loading `raw` and before `model_validate`:

```python
# Rebase relative infile to config file's directory
data_section = raw.get("data") if isinstance(raw, dict) else None
if isinstance(data_section, dict):
    infile_val = data_section.get("infile")
    if isinstance(infile_val, str) and not Path(infile_val).is_absolute():
        data_section["infile"] = str((path.parent / infile_val).resolve())
```

Also update:
- `examples/*/README.md` — step 1 uses `uv run poe generate-examples`, step 2 uses `uv run spectrafit fit <config> --noplot`
- `examples/README.md` — update usage section similarly

### Follow-up Actions

- [x] Patch `from_file()` in `fitting_config.py`
- [x] Update `examples/basic/README.md`
- [x] Update `examples/two-peak-constrained/README.md`
- [x] Update `examples/README.md`
- [x] Add/update unit test for `from_file()` path rebasing
- [x] Verify `uv run spectrafit fit examples/basic/input.toml --noplot` passes end-to-end

## Status History

| Date       | Status         | Notes                                              |
| ---------- | -------------- | -------------------------------------------------- |
| 2026-03-07 | 🔴 Not Started | Spike created and scoped                           |
| 2026-03-07 | 🟢 Complete    | Root cause found; decision made; implementation plan ready |

---

_Last updated: 2026-03-07 by Copilot_
