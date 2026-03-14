# SpectraFit v2.0.0 Migration TODO

> **Migration**: v1.x → v2.0.0
> **Status**: Complete (deferred follow-ups only)
> **Branch**: `v2.0.0`
> **Last Updated**: 2026-03-19

---

## Executive Tracker

This file is the durable migration dashboard.

Use it as the repo-visible source of truth for:

- what is finished
- what is still open
- what must run in serial order
- what can run in parallel
- what is deferred

Closeout snapshot recorded during the migration hardening push:

- `uv run poe ci` is green
- `uv run poe test-fast` is green
- `uv run --group dev pytest tests/ -q` is green (`606 passed`)
- `python scripts/scan_antipatterns.py -j` is green (no remaining findings)
- `uv run ruff check tests scripts` is green
- `CHECKLIST.md` is generated and current
- notebook bridge inventory / round-trip tests are green after the latest cleanup wave
- `zen-of-languages` health score: `14.7`
- `spectrafit.report.*` is now a frozen v2.x compatibility surface with a v3.0.0
  removal target and no internal runtime callers
- a fresh `legacy` recount shows the remaining mentions are concentrated in intentional
  boundary adapters, compatibility helpers, and frozen shim docs
- there are no remaining actionable migration blockers in-tree; mutation testing
  is explicitly deferred until the repository standardizes an approved tool

---

## Done

- Canonical `UnifiedFittingConfig` / `FitResult` pipeline seams are established.
- CLI fit persists canonical `FitResult` JSON.
- CLI report reads canonical `FitResult` directly.
- Shared `spectrafit/reporting/service.py` owns text/markdown/json rendering.
- Typed notebook export root document and typed shared solver projection are landed.
- Local decomposition is bundle-only for local fits.
- `SplitFrame` is the canonical split-frame boundary.
- Runtime postprocessing/result bridge reuse typed postprocessing fields.
- Parameter-builder ownership is re-homed to `spectrafit/models/parameter_builder.py`.
- Internal runtime callers now import `spectrafit.models.solver` directly.
- Deleted `spectrafit/models/functions/builtin.py`.
- Runtime regression metrics now return `SplitFrame` directly.
- Shared reporting runtime stats stay on `SplitFrame` through rendering.
- Loader and notebook/report runtime flow now prefer typed `context` / `fitting_mode`
  instead of legacy `global_` views.
- `UnifiedFittingConfig` now treats typed `context` as the canonical mode owner.
- Notebook config I/O now round-trips through canonical `context` / `fitting_mode`.
- Notebook config export now serializes the validated `UnifiedFittingConfig` instead of
  hand-assembling a partial TOML payload, so canonical `context`, `column`, and
  confidence-interval settings survive round-trip.
- Notebook export now owns typed `Component` models internally and projects the legacy
  notebook/report `initial_model` shape only at the final serialization boundary.
- Notebook metric projection now consumes `SplitFrame` directly, and the redundant
  `SplitFrame.coerce()` helper has been removed.
- Removed zero-usage notebook `return_*` dataframe aliases from `spectrafit/jupyter/core.py`.
- Removed stale `SolverResults.settings_*` notebook shims in favor of canonical typed accessors.
- Public shim surfaces are explicitly quarantined in tests/docs instead of being treated as
  canonical code paths.
- Canonical `FitResult` now rejects unknown top-level fields; legacy persisted
  `global_fitting` coercion remains isolated in the JSON adapter boundary.
- Raw `UnifiedFittingConfig` ingress normalization now lives in a dedicated typed
  adapter module, and the v2 `[solver]` block now fails loudly on unknown keys
  instead of silently dropping them during migration.
- Notebook preprocessing now keeps `PreprocessingConfig` as the sole internal
  owner; `args_pre` is a compatibility proxy/write-back surface instead of a
  second mutable source of truth.
- Notebook config/report boundaries now preserve canonical preprocessing
  internally and project `DataPreProcessingAPI` only at the final boundary.
- Remaining Jupyter-facing docstring type spellings now use modern Python 3.12
  syntax, and active `field_validator` sites now declare explicit modes where
  they previously relied on the default.
- The external plugin CLI now registers commands exposed by discovered plugins,
  not just listing plugin metadata.
- Stale migration narration has been tightened so canonical owners no longer describe removed
  dict-based paths as current runtime behavior.
- Phase 2 runtime cleanup has partially landed:
  - CLI runtime/config loading now uses a typed shared runtime in Typer context with
    explicit path / `SPECTRAFIT_CONFIG` / app-dir-backed resolution.
  - `fit` / `validate` now use injected runtime dependencies instead of the fit command's
    old global status path.
  - `PostProcessing.__call__()` now keeps stored input dataframe state immutable and
    returns enriched data through typed result values.
- `spectrafit.report.*` is explicitly frozen for v2.x only, with no internal
  runtime callers and a v3.0.0 removal target.
- Full-suite aggregate coverage now exceeds the migration thresholds:
  - `spectrafit/cli`: `91.86%`
  - `spectrafit/core`: `87.39%`

## Open

- Create and maintain this compact tracker as the durable migration control surface.
- No active migration implementation tasks remain.

## Current serial lane

1. Keep this `TODO.md` tracker current.
2. Avoid expanding compatibility surfaces again in new code.

## Parallel lane

- public-doc/API accuracy follow-ups beyond the Phase 6 closure slice
- historical migration notes below remain archived context, not active blockers

## Blocked / deferred

- Mutation testing for critical fitting paths is deferred until the repository
  adopts an approved mutation-testing tool/workflow.
- `spectrafit/models/functions/regular.py`
- `spectrafit/models/functions/distributions.py`
- other zen complexity/style hotspots that are real hygiene issues, but not the highest-value v1→v2 ownership blockers

## Historical migration notes

The sections below are retained as historical migration context and archive material.

---

## 🎯 Phase 1: CLI Architecture Modernization

### 1.1 Typer CLI Enhancement ✅ (Completed)

- [x] Migrate from `argparse` to `Typer`
- [x] Implement basic CLI command structure
- [x] Add `--version` callback with `typer.Exit()`

### 1.2 Legacy Code Removal 🔴 (High Priority)

- [x] **Remove deprecated function** `extracted_from_command_line_runner()` (line 369-383)
- [x] **Replace `sys.exit(1)` calls** with proper exceptions:
  - [x] `tools.py` line 82: Replace with `KeyError` exception with descriptive message
  - [x] `tools.py` line 629: Replace with `ValueError` exception with descriptive message
- [x] **Replace `input()` with Typer prompts**:
  - [x] `spectrafit.py` line 280: Use `typer.confirm()` instead of `input()`
- [x] **Use Typer enums for validation** instead of manual checks (lines 224-238)

### 1.3 Subcommands Architecture 🔴 (High Priority)

- [x] **Create subcommand structure** following Typer best practices:
  ```
  spectrafit/
  ├── cli/
  │   ├── __init__.py
  │   ├── main.py           # Main Typer app entry point
  │   ├── _types.py         # Shared Enums and type definitions
  │   ├── _callbacks.py     # Shared callbacks (version, verbose)
  │   ├── commands/
  │   │   ├── __init__.py
  │   │   ├── fit.py        # spectrafit fit <file>
  │   │   ├── validate.py   # spectrafit validate <input>
  │   │   ├── convert.py    # spectrafit convert <file>
  │   │   └── report.py     # spectrafit report <results>
  ```
- [x] Implement `spectrafit fit` as primary fitting command
- [x] Add `spectrafit validate` for input file validation
- [x] Add `spectrafit convert` for file format conversion (JSON ↔ YAML ↔ TOML)
- [x] Add `spectrafit report` for generating reports from results
- [x] Add `-h` and `--help` support: `context_settings={"help_option_names": ["-h", "--help"]}`
- [x] Create shared `Enum` classes for separator, decimal, global mode, verbose level

### 1.4 Plugin CLI Integration ✅ (Completed)

- [x] Create `spectrafit plugins` subcommand group
- [x] Add plugin discovery mechanism
- [x] Implement `spectrafit plugins list` command

---

## 🏗️ Phase 2: Architecture Refactoring

### 2.1 Module Splitting ✅ DONE (v2.0.0)

Split large modules into smaller, focused files:

#### `models/builtin.py` (1899 lines) → Split into:

- [x] `models/distributions.py` - Gaussian, Lorentzian, Voigt, PseudoVoigt
- [x] `models/solver.py` - `SolverModels` class
- [x] `models/model_parameters.py` - `ModelParameters`, `ReferenceKeys` classes
- [x] `models/types.py` - TypeAliases (`FittingArgs`, `PeaksDict`, etc.)
- [x] `models/global_fitting.py` - `GlobalMode(IntEnum)`, `GlobalFittingConfig`
- [x] `models/autopeak.py` - reduced to DeprecationWarning shim (→ removed in v2.1.0)

#### `report.py` (937 lines) → Split into:

- [x] `report/metrics.py` - `RegressionMetrics` class
- [x] `report/formatter.py` - `fit_report_as_dict` and formatting functions
- [x] `report/printer.py` - `PrintingResults`, `PrintingStatus` classes
- [x] `report/confidence.py` - Confidence interval calculations

#### `tools.py` (769 lines) → Split into:

- [x] `core/data_loader.py` - `load_data`, `read_input_file`
- [x] `core/preprocessing.py` - `PreProcessing` class
- [x] `core/postprocessing.py` - `PostProcessing` class
- [x] `core/export.py` - `SaveResult` class

#### `plugins/notebook.py` (1412 lines) → Split into:

- [x] `plugins/notebook/display.py` - `DataFrameDisplay` class
- [x] `plugins/notebook/plotting.py` - `DataFramePlot` class
- [x] `plugins/notebook/export.py` - `ExportResults`, `ExportReport` classes
- [x] `plugins/notebook/solver.py` - `SolverResults` class
- [x] `plugins/notebook/core.py` - `SpectraFitNotebook` class

### 2.2 Separation of Concerns ✅ DONE (v2.0.0)

`FittingPipeline` implemented in `spectrafit/core/pipeline.py`:

- [x] `UnifiedFittingConfig` — single validated entry point (`spectrafit/core/fitting_config.py`)
- [x] v1.x backward compat via `@model_validator(mode="before")` `migrate_v1_format`
- [x] `FittingPipeline` accepts `UnifiedFittingConfig | dict`; wires into existing pipeline stages
- [x] CLI converged: `spectrafit/cli/commands/fit.py` builds `UnifiedFittingConfig` directly
- [x] `testpaths = ["tests"]` — new `tests/` tree at repo root; legacy `spectrafit/*/test/` removed
- [x] CLI fit tests green: 58 passed, 0 xfailed (`tests/integration/test_cli_fit.py`)

- [x] **CLI Layer** (`spectrafit/cli/`): pure argument parsing, delegates to `FittingPipeline`
- [x] **API Layer** (`spectrafit/api/`): Pydantic v2 models for all interfaces
- [x] **Core Layer** (`spectrafit/core/`): `FittingPipeline`, `UnifiedFittingConfig`, pre/post processing
- [x] **Reporting Layer** (`spectrafit/report/`): result formatting and export coordination

### 2.3 Remove Side Effects ✅ DONE

- [x] `PreProcessing.__call__()` no longer mutates raw `args`; the compatibility shim now
  delegates to the pure `preprocess()` entry point
- [x] `PostProcessing.__call__()` no longer mutates stored runtime state; it returns an
  immutable typed `PostProcessingResult`
- [x] Global CLI status state is injected through runtime dependencies instead of a global
  `__status__` path

### 2.4 Dependency Injection Pattern ✅ DONE

- [x] Implement configuration injection for fitting routines
- [x] Use Typer context for shared state where needed
- [x] Create factory functions for complex objects
- [x] Replace global `__status__` with injected `StatusPrinter`

### 2.5 Configuration Management ✅ DONE

- [x] Create unified configuration loader
- [x] Support environment variables for settings
- [x] Implement `typer.get_app_dir()` for config storage
- [x] Add configuration validation with Pydantic v2

---

## 🔧 Phase 3: Pydantic v2 Consistency

> **Current reality:** the original Phase 3 checklist below is partly historical.
> The real landed work now includes confidence-interval ownership cleanup,
> `ConfIntervalAPI` quarantine, `FitResult` root hardening, and typed config-ingress
> normalization with strict v2 `[solver]` validation, plus notebook-side canonical
> preprocessing ownership with compatibility projection only at the final
> notebook/report boundary. The Phase 3 audit is now complete for active runtime
> paths; the checklist below is retained as historical context and reconciled to
> the current architecture.

### 3.1 Fix Deprecated Patterns 🟡 (Medium Priority)

| File | Line | Current | Target |
|------|------|---------|--------|
| ~~`plugins/notebook.py`~~ | ~~1303~~ | ~~`.dict(exclude_none=True)`~~ | ~~`.model_dump(exclude_none=True)`~~ ✅ |
| Various docstrings | - | `Dict[str, Any]` | `dict[str, Any]` |

- [x] Run search for `.dict()` and replace with `.model_dump()`
- [x] Update all docstrings to use modern type hint syntax
- [x] Verify all `field_validator` decorators use `mode="before"` or `mode="after"` correctly

### 3.2 Model Audit ✅ DONE

- [x] Audit all existing Pydantic models for v2 compatibility
- [x] Verify patterns are correct:
  - [x] `validator` → `field_validator` ✅ (already done)
  - [x] `root_validator` → `model_validator` ✅ (already done)
  - [x] `Config` class → `model_config` ✅ (already done)
- [x] Ensure `.model_dump()` used everywhere instead of deprecated `.dict()`
- [x] Keep notebook preprocessing on canonical `PreprocessingConfig` internally and
  project `DataPreProcessingAPI` only at the notebook/report boundary

### 3.3 Reconciled model ownership ✅ DONE

- [x] `CLIConfig` responsibility is covered by `CliRuntimeSettings` plus typed CLI
  option models
- [x] `FittingConfig` responsibility is covered by `UnifiedFittingConfig`
- [x] `OutputConfig` exists as `spectrafit.models.output_config.OutputConfig`
- [x] `PipelineConfig` responsibilities are split across `UnifiedFittingConfig`,
  `OutputConfig`, and `PipelineDependencies`
- [x] Active canonical models already use `Annotated` / `Field()` descriptions where
  the current architecture requires them

---

## 🔌 Phase 4: Plugin Architecture

### 4.1 Plugin System Design 🟡 (Medium Priority)

Current issues:
- No plugin interface/protocol (✅ Resolved: Protocol added)
- No dynamic plugin discovery (✅ Resolved: Discovery system implemented)
- Discovered plugins were listed but not wired into callable CLI commands
  (✅ Resolved: command registration helper added)

- [x] Research plugin patterns:
  - [x] Entry points (`[project.entry-points]`)
  - [x] Dynamic discovery via `importlib.metadata`
  - [x] Lazy loading with `importlib.metadata.EntryPoint.load()`

- [x] Design plugin interface:
  ```python
  from typing import Protocol
  import typer

  class SpectraFitPlugin(Protocol):
      """Protocol for SpectraFit plugins."""

      name: str
      version: str
      description: str

      def register_commands(self, parent_app: typer.Typer) -> None:
          """Register CLI commands with the parent Typer app."""
          ...

      def register_models(self) -> list[type]:
          """Return list of Pydantic models this plugin provides."""
          ...
  ```

### 4.2 Built-in Plugins

- [x] Finalize plugin policy: the shipped plugin framework is for **external**
  entry-point plugins; Jupyter remains a top-level interface and Mössbauer plugin
  entry points remain out of the core package
- [x] Reconcile ADRs and plugin docs so they stop implying built-in plugin entry
  points currently ship in `spectrafit`

### 4.3 Plugin Documentation

- [x] Document plugin creation guide
- [x] Add plugin development examples
- [x] Create a repository-owned plugin template

---

## 🧪 Phase 5: Testing Enhancement

### 5.1 CLI Testing 🟡 (Medium Priority)

- [x] Use `typer.testing.CliRunner` for CLI tests
- [x] Add focused command-behavior coverage across supported subcommands
- [x] Test error exit codes (0 for success, non-zero for errors)
- [x] Test help output format (`--help`, `-h`)
- [x] Test version output (`--version`, `-v`)

Example test structure:
```python
from typer.testing import CliRunner
from spectrafit.cli.main import app

runner = CliRunner()

def test_fit_command_success():
    result = runner.invoke(app, ["fit", "data.csv", "-i", "input.toml"])
    assert result.exit_code == 0

def test_fit_command_invalid_file():
    result = runner.invoke(app, ["fit", "nonexistent.csv"])
    assert result.exit_code != 0
    assert "Error" in result.output
```

### 5.2 Integration Testing

- [x] Test complete fitting workflows (end-to-end)
- [x] Test plugin loading and discovery
- [x] Test configuration precedence (CLI path > env config > default config)
- [x] Replace v1.x CLI compatibility expectations with migration docs and focused
  supported-surface tests

### 5.3 Post-migration Coverage Hardening

- [x] Achieve >90% coverage for CLI layer
- [x] Achieve >85% coverage for core fitting
- [x] Evaluate mutation testing for critical paths; deferred until an approved
  mutation-testing tool/workflow exists in the repository

---

## 📚 Phase 6: Documentation

### 6.1 CLI Documentation 🟢 (Low Priority)

- [x] Update usage documentation for new CLI structure
- [x] Add subcommand reference pages
- [x] Create migration guide from v1.x CLI
- [x] Document supported CLI options with examples

### 6.2 Architecture Documentation

- [ ] Create architecture decision records (ADRs):
  - [x] ADR-001: Typer CLI Migration
  - [x] ADR-002: Plugin Architecture
  - [x] ADR-003: Subcommand Structure
  - [x] ADR-004: Module Splitting Strategy
- [x] Add C4-style architecture diagram coverage (Mermaid)
- [x] Document component responsibilities

### 6.3 API Documentation

- [x] Repoint API pages to canonical v2 modules and surfaces
- [x] Surface the current module/documentation structure in MkDocs navigation
- [x] Add type stub generation (`py.typed` marker)
- [x] Create API changelog for v2.0.0

---

## 🚀 Phase 7: Release Preparation

### 7.1 Breaking Changes Documentation

Document all breaking changes:

| Change | v1.x | v2.0.0 | Migration |
|--------|------|--------|-----------|
| CLI structure | `spectrafit file.csv` | `spectrafit fit file.csv` | Add `fit` subcommand |
| Interactive mode | `input()` prompts | `typer.confirm()` | Automatic |
| Config format | Mixed | Unified TOML | Converter provided |

- [x] Document all breaking changes in CHANGELOG
- [x] Create deprecation warnings for v1.x patterns
- [x] Add migration scripts if needed

### 7.2 Version Bump

- [x] Update `pyproject.toml` version to `2.0.0`
- [x] Update `CITATION.cff`
- [x] Update Docker image tags
- [x] Update `__version__` in `__init__.py`

### 7.3 Release Notes

- [x] Write comprehensive v2.0.0 release notes
- [x] Highlight new features
- [x] Document upgrade path
- [x] Add performance benchmarks (v1.x vs v2.0.0)

---

## 📊 Gap Analysis Summary (Updated)

| Area | Current State (v1.x) | Target State (v2.0.0) | Priority | Effort | Status |
|------|---------------------|----------------------|----------|--------|--------|
| CLI | Single command + `input()` | Subcommands + Typer prompts | 🔴 High | Medium | ✅ Done (fit, validate, convert, report) |
| Architecture | Monolithic (`fitting_routine`) | Pipeline pattern | 🔴 High | High | 🔄 Pending |
| Module Size | Large files (769-1899 lines) | Split modules (<300 lines) | 🔴 High | Medium | 🔄 Pending |
| Error Handling | Mixed `sys.exit`/`typer.Exit` | Consistent exceptions | 🔴 High | Low | ✅ Done |
| Pydantic | 1 deprecated `.dict()` call | Pure v2 patterns | 🟡 Medium | Low | ✅ Done |
| Plugins | Separate Typer apps | External plugin protocol + template | 🟡 Medium | Medium | ✅ Done |
| Testing | Good coverage | CLI-focused tests + coverage hardening | 🟢 Low | Medium | 🔄 Partial |
| Documentation | Complete | Updated for v2 | 🟢 Low | Medium | ✅ Done |

---

## 🔗 References

- [Typer Documentation](https://typer.tiangolo.com/)
- [Typer Subcommands Tutorial](https://typer.tiangolo.com/tutorial/subcommands/)
- [Typer Testing](https://typer.tiangolo.com/tutorial/testing/)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Python Plugin Systems](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
- [Python 2025 Best Practices](https://nerdleveltech.com/python-best-practices-the-2025-guide-for-clean-fast-and-secure-code/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

---

## 📝 Notes

### Typer Best Practices Applied

1. **Use `Annotated` types** for all CLI parameters ✅
2. **Separate subcommands** into modules under `commands/` ✅
3. **Use `app.add_typer()`** for nested command groups
4. **Implement `--version`** with `is_eager=True` callback ✅
5. **Add both `-h` and `--help`** via context settings ✅
6. **Return proper exit codes** (0 success, non-zero errors) ✅
7. **Use `typer.echo()`** for output (Rich integration) ✅
8. **Use `typer.confirm()`** instead of `input()` for prompts ✅
9. **Use `Enum` classes** for constrained choices ✅
10. **Use `CliRunner`** for testing

### Python 2025 Best Practices

1. **Use `src/` layout** for package isolation
2. **Use `pyproject.toml`** for all configuration ✅
3. **Enforce style** with Ruff and Black ✅
4. **Add type hints** and run mypy ✅
5. **Write tests** and automate in CI ✅
6. **Use modern typing syntax** (`dict[str, Any]` not `Dict[str, Any]`)

### Migration Checklist

- [ ] All `sys.exit()` calls removed from business logic
- [ ] All argparse code removed ✅
- [ ] All CLI tests use `CliRunner`
- [ ] All `.dict()` calls replaced with `.model_dump()`
- [ ] Backward compatibility tested with v1.x input files
- [ ] Performance benchmarks pass
- [ ] Documentation updated

---

*Last Updated: 2025-11-30*
