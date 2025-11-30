# SpectraFit v2.0.0 Migration TODO

> **Migration**: v1.x → v2.0.0
> **Status**: In Progress
> **Branch**: `v2.0.0`
> **Last Updated**: 2025-11-28

---

## 📋 Overview

This document tracks the migration tasks for SpectraFit from v1.x to v2.0.0, focusing on:

- Modern CLI architecture with Typer
- Clean separation of concerns
- Enhanced plugin architecture
- Pydantic v2 consistency
- Improved testing and documentation

---

## 🔍 Current Codebase Analysis (Legacy Issues)

### Critical Issues Identified

#### 1. Monolithic CLI Structure (`spectrafit/spectrafit.py` - 413 lines)

| Issue | Location | Description |
|-------|----------|-------------|
| Single command | `cli_main()` | All operations in one command instead of subcommands |
| ~~Interactive loop~~ | ~~`run_fitting_workflow()`~~ | ~~Uses `input()` for user interaction instead of Typer prompts~~ ✅ |
| ~~Deprecated code~~ | ~~`extracted_from_command_line_runner()`~~ | ~~Raises `RuntimeError` - should be removed~~ ✅ |
| ~~Manual validation~~ | ~~Lines 224-238~~ | ~~Hardcoded validation instead of Typer `Enum` or `callback`~~ ✅ |

#### 2. Legacy Python Patterns

| File | Line | Issue | Fix |
|------|------|-------|-----|
| ~~`tools.py`~~ | ~~82~~ | ~~`sys.exit(1)` in `PreProcessing.__call__`~~ | ~~Use exceptions~~ ✅ |
| ~~`tools.py`~~ | ~~629~~ | ~~`sys.exit(1)` in business logic~~ | ~~Use exceptions~~ ✅ |
| ~~`spectrafit.py`~~ | ~~280~~ | ~~`input("Would you like...")`~~ | ~~Use `typer.confirm()`~~ ✅ |
| Docstrings | Various | `Dict[str, Any]` style | Update to modern `dict[str, Any]` |

#### 3. Pydantic v2 Inconsistencies

| File | Line | Issue | Fix |
|------|------|-------|-----|
| ~~`plugins/notebook.py`~~ | ~~1303~~ | ~~Uses `.dict(exclude_none=True)`~~ | ~~Use `.model_dump(exclude_none=True)`~~ ✅ |
| ~~`plugins/notebook.py`~~ | ~~893~~ | ~~Docstring mentions `.dict()`~~ | ~~Update documentation~~ ✅ |

#### 4. Tight Coupling Issues

| Component | Responsibilities | Recommended Split |
|-----------|-----------------|-------------------|
| `fitting_routine()` | Load, preprocess, solve, postprocess, print | Split into pipeline stages |
| `PreProcessing` | Processing + Args mutation | Separate concerns |
| `PostProcessing` | 7+ responsibilities | Extract to single-responsibility classes |
| `PlotSpectra` | Tightly coupled to workflow | Make independent |

#### 5. Large Modules Requiring Refactoring

| Module | Lines | Issues | Recommendation |
|--------|-------|--------|----------------|
| `models/builtin.py` | 1899 | Too many models in one file | Split by model family |
| `report.py` | 937 | Multiple responsibilities | Split into reporter classes |
| `tools.py` | 769 | Mixed concerns | Split: data loading, preprocessing, export |
| `plugins/notebook.py` | 1412 | Monolithic class | Split into smaller components |
| `plugins/rixs_visualizer.py` | 727 | Own Typer app | Integrate as plugin |

#### 6. Code Hygiene Score: 83/100

- **Deep nesting** (6 levels detected) - needs refactoring
- **Comment-to-code ratio** < 10% - add more explanatory comments
- **Mixed error handling** - some `typer.Exit()`, some `sys.exit()`

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
- [x] Migrate RIXS visualizer: `spectrafit plugins rixs`
- [ ] Refactor `rixs_visualizer.py` (727 lines) - remove separate `app_cli` Typer instance (kept for backward compatibility)
- [x] Add plugin discovery mechanism
- [x] Implement `spectrafit plugins list` command

---

## 🏗️ Phase 2: Architecture Refactoring

### 2.1 Module Splitting 🔴 (High Priority)

Split large modules into smaller, focused files:

#### `models/builtin.py` (1899 lines) → Split into:

- [ ] `models/distributions.py` - Gaussian, Lorentzian, Voigt, PseudoVoigt
- [ ] `models/cumulative.py` - Cumulative distribution models
- [ ] `models/special.py` - Step functions, exponential, polynomial
- [ ] `models/solver.py` - `SolverModels` class
- [ ] `models/autopeak.py` - Auto-peak detection logic

#### `report.py` (937 lines) → Split into:

- [ ] `report/metrics.py` - `RegressionMetrics` class
- [ ] `report/formatter.py` - `fit_report_as_dict` and formatting functions
- [ ] `report/printer.py` - `PrintingResults`, `PrintingStatus` classes
- [ ] `report/confidence.py` - Confidence interval calculations

#### `tools.py` (769 lines) → Split into:

- [ ] `core/data_loader.py` - `load_data`, `read_input_file`
- [ ] `core/preprocessing.py` - `PreProcessing` class
- [ ] `core/postprocessing.py` - `PostProcessing` class
- [ ] `core/export.py` - `SaveResult` class

#### `plugins/notebook.py` (1412 lines) → Split into:

- [ ] `plugins/notebook/display.py` - `DataFrameDisplay` class
- [ ] `plugins/notebook/plotting.py` - `DataFramePlot` class
- [ ] `plugins/notebook/export.py` - `ExportResults`, `ExportReport` classes
- [ ] `plugins/notebook/solver.py` - `SolverResults` class
- [ ] `plugins/notebook/core.py` - `SpectraFitNotebook` class

### 2.2 Separation of Concerns 🔴 (High Priority)

Refactor `fitting_routine()` from monolithic function to pipeline:

```python
# Current (monolithic):
def fitting_routine(args):
    df = load_data(args)
    df, args = PreProcessing(df, args)()
    minimizer, result = SolverModels(df, args)()
    df, args = PostProcessing(df, args, minimizer, result)()
    PrintingResults(args, minimizer, result)()
    return df, args

# Target (pipeline):
class FittingPipeline:
    def __init__(self, config: FittingConfig):
        self.loader = DataLoader(config.input)
        self.preprocessor = Preprocessor(config.preprocessing)
        self.solver = Solver(config.optimizer, config.minimizer)
        self.reporter = Reporter(config.output)

    def run(self) -> FittingResult:
        data = self.loader.load()
        processed = self.preprocessor.process(data)
        result = self.solver.solve(processed)
        return self.reporter.format(result)
```

- [ ] **CLI Layer** (`spectrafit/cli/`):
  - [ ] Pure argument parsing and validation
  - [ ] No business logic in CLI handlers
  - [ ] Delegate to API layer

- [ ] **API Layer** (`spectrafit/api/`):
  - [ ] Pydantic v2 models for all interfaces
  - [ ] Input/output data contracts
  - [ ] Validation logic

- [ ] **Core Layer** (`spectrafit/core/`):
  - [ ] Fitting algorithms
  - [ ] Peak models
  - [ ] Mathematical operations

- [ ] **Reporting Layer** (`spectrafit/report/`):
  - [ ] Result formatting
  - [ ] Export functionality
  - [ ] Visualization coordination

### 2.3 Remove Side Effects

- [ ] `PreProcessing.__call__()` modifies `args` dict - return new dict instead
- [ ] `PostProcessing.__call__()` modifies `self.df` and `self.args` - make immutable
- [ ] Global state `__status__` in `spectrafit.py` - inject as dependency

### 2.4 Dependency Injection Pattern

- [ ] Implement configuration injection for fitting routines
- [ ] Use Typer context for shared state where needed
- [ ] Create factory functions for complex objects
- [ ] Replace global `__status__` with injected `StatusPrinter`

### 2.5 Configuration Management

- [ ] Create unified configuration loader
- [ ] Support environment variables for settings
- [ ] Implement `typer.get_app_dir()` for config storage
- [ ] Add configuration validation with Pydantic v2

---

## 🔧 Phase 3: Pydantic v2 Consistency

### 3.1 Fix Deprecated Patterns 🟡 (Medium Priority)

| File | Line | Current | Target |
|------|------|---------|--------|
| ~~`plugins/notebook.py`~~ | ~~1303~~ | ~~`.dict(exclude_none=True)`~~ | ~~`.model_dump(exclude_none=True)`~~ ✅ |
| Various docstrings | - | `Dict[str, Any]` | `dict[str, Any]` |

- [x] Run search for `.dict()` and replace with `.model_dump()`
- [ ] Update all docstrings to use modern type hint syntax
- [ ] Verify all `field_validator` decorators use `mode="before"` or `mode="after"` correctly

### 3.2 Model Audit

- [ ] Audit all existing Pydantic models for v2 compatibility
- [ ] Verify patterns are correct:
  - [x] `validator` → `field_validator` ✅ (already done)
  - [x] `root_validator` → `model_validator` ✅ (already done)
  - [x] `Config` class → `model_config` ✅ (already done)
- [x] Ensure `.model_dump()` used everywhere instead of deprecated `.dict()`

### 3.3 New Models

- [ ] Create `CLIConfig` model for CLI arguments (replace raw `dict`)
- [ ] Create `FittingConfig` model for fitting parameters
- [ ] Create `OutputConfig` model for output settings
- [ ] Create `PipelineConfig` model for full workflow configuration
- [ ] Ensure all models use `Annotated` types with `Field()` descriptions

---

## 🔌 Phase 4: Plugin Architecture

### 4.1 Plugin System Design 🟡 (Medium Priority)

Current issues:
- `plugins/rixs_visualizer.py` has its own `app_cli = typer.Typer()` (line 40)
- No plugin interface/protocol
- No dynamic plugin discovery

- [ ] Research plugin patterns:
  - [ ] Entry points (`[project.entry-points]`)
  - [ ] Dynamic discovery via `importlib.metadata`
  - [ ] Lazy loading with `importlib.import_module`

- [ ] Design plugin interface:
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

- [ ] Convert RIXS visualizer to plugin architecture
  - [ ] Remove standalone `app_cli` Typer app from `rixs_visualizer.py`
  - [ ] Implement `RIXSPlugin` class following `SpectraFitPlugin` protocol
- [ ] Convert Jupyter integration to plugin
  - [ ] Split `notebook.py` (1412 lines) into modular plugin
- [ ] Create Mössbauer plugin from existing models

### 4.3 Plugin Documentation

- [ ] Document plugin creation guide
- [ ] Add plugin development examples
- [ ] Create plugin template (cookiecutter or copier)

---

## 🧪 Phase 5: Testing Enhancement

### 5.1 CLI Testing 🟡 (Medium Priority)

- [ ] Use `typer.testing.CliRunner` for CLI tests
- [ ] Add parametrized tests for all subcommands
- [ ] Test error exit codes (0 for success, non-zero for errors)
- [ ] Test help output format (`--help`, `-h`)
- [ ] Test version output (`--version`, `-v`)

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

- [ ] Test complete fitting workflows (end-to-end)
- [ ] Test plugin loading and discovery
- [ ] Test configuration precedence (CLI > file > defaults)
- [ ] Test backward compatibility with v1.x input files

### 5.3 Coverage Goals

- [ ] Achieve >90% coverage for CLI layer
- [ ] Achieve >85% coverage for core fitting
- [ ] Add mutation testing for critical paths (fitting algorithms)

---

## 📚 Phase 6: Documentation

### 6.1 CLI Documentation 🟢 (Low Priority)

- [ ] Update usage documentation for new CLI structure
- [ ] Add subcommand reference pages
- [ ] Create migration guide from v1.x CLI
- [ ] Document all CLI options with examples

### 6.2 Architecture Documentation

- [ ] Create architecture decision records (ADRs):
  - [ ] ADR-001: Typer CLI Migration
  - [ ] ADR-002: Plugin Architecture
  - [ ] ADR-003: Subcommand Structure
  - [ ] ADR-004: Module Splitting Strategy
- [ ] Add C4 architecture diagrams (Mermaid)
- [ ] Document component responsibilities

### 6.3 API Documentation

- [ ] Update mkdocstrings configuration for new module structure
- [ ] Add type stub generation (`py.typed` marker)
- [ ] Create API changelog for v2.0.0

---

## 🚀 Phase 7: Release Preparation

### 7.1 Breaking Changes Documentation

Document all breaking changes:

| Change | v1.x | v2.0.0 | Migration |
|--------|------|--------|-----------|
| CLI structure | `spectrafit file.csv` | `spectrafit fit file.csv` | Add `fit` subcommand |
| Interactive mode | `input()` prompts | `typer.confirm()` | Automatic |
| Plugin CLI | `rixs-visualizer` | `spectrafit plugins rixs` | Update scripts |
| Config format | Mixed | Unified TOML | Converter provided |

- [ ] Document all breaking changes in CHANGELOG
- [ ] Create deprecation warnings for v1.x patterns
- [ ] Add migration scripts if needed

### 7.2 Version Bump

- [ ] Update `pyproject.toml` version to `2.0.0`
- [ ] Update `CITATION.cff`
- [ ] Update Docker image tags
- [ ] Update `__version__` in `__init__.py`

### 7.3 Release Notes

- [ ] Write comprehensive v2.0.0 release notes
- [ ] Highlight new features
- [ ] Document upgrade path
- [ ] Add performance benchmarks (v1.x vs v2.0.0)

---

## 📊 Gap Analysis Summary (Updated)

| Area | Current State (v1.x) | Target State (v2.0.0) | Priority | Effort | Status |
|------|---------------------|----------------------|----------|--------|--------|
| CLI | Single command + `input()` | Subcommands + Typer prompts | 🔴 High | Medium | ✅ Done (fit, validate, convert, report) |
| Architecture | Monolithic (`fitting_routine`) | Pipeline pattern | 🔴 High | High | 🔄 Pending |
| Module Size | Large files (769-1899 lines) | Split modules (<300 lines) | 🔴 High | Medium | 🔄 Pending |
| Error Handling | Mixed `sys.exit`/`typer.Exit` | Consistent exceptions | 🔴 High | Low | ✅ Done |
| Pydantic | 1 deprecated `.dict()` call | Pure v2 patterns | 🟡 Medium | Low | ✅ Done |
| Plugins | Separate Typer apps | Unified plugin protocol | 🟡 Medium | Medium | 🔄 Pending |
| Testing | Good coverage | CLI-focused tests | 🟢 Low | Medium | 🔄 Pending |
| Documentation | Complete | Updated for v2 | 🟢 Low | Medium | 🔄 Pending |

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

- [x] All `sys.exit()` calls removed from business logic
- [x] All argparse code removed ✅
- [ ] All CLI tests use `CliRunner`
- [x] All `.dict()` calls replaced with `.model_dump()`
- [ ] Backward compatibility tested with v1.x input files
- [ ] Performance benchmarks pass
- [ ] Documentation updated

---

*Last Updated: 2025-11-30*
