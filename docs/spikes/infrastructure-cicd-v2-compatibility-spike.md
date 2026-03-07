---
title: "CI/CD Pipeline v2.0.0 Compatibility"
category: "Infrastructure"
status: "🔴 Not Started"
priority: "High"
timebox: "1 sprint"
created: 2026-03-07
updated: 2026-03-07
owner: ""
tags: ["technical-spike", "infrastructure", "cicd", "github-actions"]
---

# CI/CD Pipeline v2.0.0 Compatibility

## Summary

**Spike Objective:** Identify all broken or incompatible GitHub Actions workflows after the v2.0.0
refactor and produce a minimal, correct CI/CD pipeline that passes on the `v2.0.0` branch.

**Why This Matters:** The v2.0.0 migration replaced `pip`/`setup.py`/`pylint` with `uv`/`ruff`/`mypy`
and restructured `tests/` from per-module directories to a canonical `tests/` tree. Every workflow
that references legacy tooling or paths is currently failing or silently incorrect, blocking the
branch from being mergeable.

**Timebox:** 1 sprint

**Decision Deadline:** Before `v2.0.0` PR is opened against `main`.

---

## Research Question(s)

**Primary Question:** Which workflows must be changed, deprecated, or created to make the `v2.0.0`
branch fully green in CI?

**Secondary Questions:**

- Which actions/versions are pinned to outdated commits and need bumping?
- Should `pylint.yml` be removed entirely or replaced with a ruff-check workflow?
- Can `conda-check.yml` be retained as-is (install-only smoke test) or must it be disabled until
  v2 is published to conda-forge?
- Does `--validation-report` require a separate pytest plugin, and if so, is it installed?
- Should `release-cd.yml` migrate to `uv build` + `uv publish` (trusted OIDC publisher) instead of
  `pip install build` + legacy TWINE_TOKEN?

---

## Investigation Plan

### Research Tasks

- [ ] Audit all 14 workflow files for v1-isms: `pip install`, `setup-python` without `uv`,
      `pylint`, `spectrafit/*/test/` paths
- [ ] Confirm `--validation-report` pytest flag: check if `pytest-json-report` or `pytest-html`
      is in `[project.optional-dependencies]` or `[dependency-groups.dev]` in `pyproject.toml`
- [ ] Check whether pre-commit hooks cover `ruff` + `mypy` (making separate CI steps redundant)
- [ ] Review action pin SHA vs current release for: `actions/checkout`, `setup-uv`,
      `actions/upload-artifact`, `codecov/codecov-action`
- [ ] Test `uv build` + `uv publish --trusted-publishing` flow for PyPI (OIDC vs TWINE_TOKEN)
- [ ] Verify conda-forge feedstock status for spectrafit v2 to decide whether to keep/disable
      `conda-check.yml`
- [ ] Prototype a minimal `python-ci.yml` that runs `uv run poe ci` as a single gate step
- [ ] Create proof-of-concept workflow update on a scratch branch to verify it passes

### Success Criteria

**This spike is complete when:**

- [ ] All known broken workflows are identified and categorised (remove / replace / update)
- [ ] `python-ci.yml` runs `uv run poe ci` (ruff + mypy + pytest) as the authoritative gate
- [ ] `pylint.yml` is replaced by a `ruff-check.yml` that uses `uv` and `ruff check spectrafit/`
- [ ] `release-cd.yml` uses `uv build` and trusted-publisher OIDC (no legacy token)
- [ ] `validation` job in `python-ci.yml` has the correct pytest plugin for report generation
- [ ] Python 3.13 is added to the test matrix
- [ ] `v2.0.0` branch added to `push.branches` in all relevant workflows
- [ ] All workflows pass on a test PR targeting `v2.0.0`

---

## Technical Context

**Related Components:**
- `.github/workflows/` (all 14 files)
- `pyproject.toml` (`[tool.poe.tasks]`, `[project.optional-dependencies]`, matrix Python versions)
- `tests/` (canonical test tree, no longer `spectrafit/*/test/`)
- `scripts/` (new CLI tooling: `migrate_v1_to_v2.py`)

**Dependencies:**
- Phase 6 (export.py unfreezing) is NOT required — CI fixes can land on any open PR
- `examples/` spike should land before or alongside CI changes (validation job will reference
  example fixtures if we add fixture-based smoke tests)

**Constraints:**
- All action SHA pins must be kept (security policy). Update the SHA if bumping version.
- `if: github.repository == 'Anselmoo/spectrafit'` guards must be preserved on all jobs.
- The `poe ci` task is the single source of truth for pass/fail — CI should invoke it, not
  duplicate its logic inline.

---

## Findings (fill in during spike)

### Confirmed Issues (pre-investigation)

| Workflow | Issue | Severity |
|----------|-------|----------|
| `pylint.yml` | Uses `pip install pylint` + bare `pylint` — v2 uses ruff | 🔴 Critical |
| `python-ci.yml` | `push.branches` missing `v2.0.0` | 🔴 Critical |
| `python-ci.yml` | `--validation-report` flag unresolved (no plugin in pyproject.toml) | 🟠 High |
| `python-ci.yml` | Python 3.13 absent from matrix | 🟡 Medium |
| `python-ci.yml` | No `ruff` or `mypy` step (only pre-commit + pytest) | 🟡 Medium |
| `release-cd.yml` | Uses `pip install build` + TWINE_TOKEN instead of `uv` + OIDC | 🟠 High |
| `conda-check.yml` | Triggers on ALL pushes; v2 not yet on conda-forge | 🟡 Medium |
| `devcontainer-ci.yml` | Only triggers on `main` (no v2.0.0 coverage) | 🟡 Medium |
| `docker-ci.yml` | Only triggers on `main` push | 🟡 Medium |

### Prototype/Testing Notes

_Fill in during spike execution._

### External Resources

- [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv) — current action version
- [uv publish docs](https://docs.astral.sh/uv/guides/publish/) — trusted publisher OIDC flow
- [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) — replaces TWINE_TOKEN
- [pytest-json-report](https://github.com/numirias/pytest-json-report) — for `--json-report`
- [GitHub Actions: adding Python to matrix](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners/supported-software#python)

---

## Decision

### Recommendation

_To be filled in after investigation._

**Proposed approach (preliminary):**

1. **Delete `pylint.yml`** — replace with `ruff-check.yml` using `uv run ruff check spectrafit/`
2. **Update `python-ci.yml`**: add `v2.0.0` to push branches; add Python 3.13; replace
   inline pytest call with `uv run poe ci`; fix validation report plugin
3. **Update `release-cd.yml`**: replace `pip install build` with `uv sync --group build`;
   use `uv build` + `uv publish`; migrate to OIDC trusted publisher
4. **Disable `conda-check.yml`** (add `if: false`) until v2 lands on conda-forge
5. **Retain** `docker-ci.yml`, `devcontainer-ci.yml`, `codeql.yml`, `dependency-review.yml`,
   `release-drafter.yml`, `greetings.yml`, `labeler.yml` with minor branch/SHA updates

### Follow-up Actions

- [ ] Open PR with workflow updates against `v2.0.0` branch
- [ ] Add `pytest-json-report` (or remove the `--validation-report` flag) in `pyproject.toml`
- [ ] Update architecture docs to reflect canonical CI gate (`poe ci`)
- [ ] Create GitHub issue for conda-forge feedstock update when v2.0.0 is released

---

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2026-03-07 | 🔴 Not Started | Spike created from v2.0.0 audit |

---

_Last updated: 2026-03-07_
