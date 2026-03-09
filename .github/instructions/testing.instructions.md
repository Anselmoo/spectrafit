---
applyTo: "tests/**/*.py,spectrafit/**/test/**/*.py"
---

# SpectraFit Testing Guide

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures: energy_axis, sample_*_spectrum,
│                            # tmp_output_dir, sample_dataframe, custom markers
├── unit/                    # Fast unit tests (<1 s, no I/O) — pytest marker: @pytest.mark.unit
│   ├── test_types.py        # TypeAlias sanity
│   ├── test_naming.py       # lmfit_param_name / sanitize_component_id / translate_dot_notation
│   ├── test_fitting_config.py   # UnifiedFittingConfig
│   ├── test_fitting_config_phase65.py  # computed fields: components, context, build_composite_model
│   ├── test_fitting_context.py  # FittingContext / FittingMode / EnvironmentMode / detect_environment
│   ├── test_data_config.py  # DataConfig
│   ├── test_bundle.py       # CompositeModelBundle / build_composite_bundle
│   ├── test_peak_models.py  # FitParameter / Component
│   ├── test_model_parameters.py  # ModelParameters (post-rehoming)
│   ├── test_global_fitting.py   # GlobalFittingConfig
│   ├── test_registry.py    # ReferenceKeys.model_check(), ModelInfo
│   ├── test_fit_result_extended.py  # FitInsights, DataSummary, ConfidenceResults, FitResult.from_legacy_dict
│   ├── test_solver_results.py   # SolverResults.from_fitting_args(), all property delegates
│   ├── test_init_command.py     # InitConfig, InitEnvironment, _run_init, CLI flag integration
│   └── test_banner.py           # render_startup_panel TTY-gate, _env_label colours
├── integration/             # Pipeline + CLI end-to-end — pytest marker: @pytest.mark.integration
│   ├── test_pipeline.py     # FittingPipeline with UnifiedFittingConfig
│   ├── test_cli_fit.py      # CLI fit subcommand
│   ├── test_v1_compat.py   # rixs/config.json backward-compat smoke test
│   └── test_init_workflow.py   # spectrafit init e2e: project creation, formats, overwrite
└── validation/              # Scientific correctness — pytest marker: @pytest.mark.validation
    ├── test_analytical.py
    └── test_numerical_stability.py
```

## Active Test Suite

The active test suite is `tests/` only. `testpaths = ["tests"]` is set in `pyproject.toml`.

**Legacy test dirs** (`spectrafit/*/test/`) are **excluded from CI runs** and scheduled for
deletion once each module is migrated.

## Running Tests

```bash
# Full suite (canonical CI gate)
uv run poe ci

# Tests only
uv run poe test

# Fast tests (skip @pytest.mark.slow)
uv run poe test-fast

# With coverage
uv run poe test-cov

# Direct pytest (when poe unavailable)
uv run pytest tests/ -v
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
```

## Pytest Markers

Register markers in `pyproject.toml` under `[tool.pytest.ini_options]`. Use them to
categorise tests:

```python
@pytest.mark.unit
@pytest.mark.parametrize("x,expected", [...])
def test_something(x, expected): ...

@pytest.mark.integration
def test_pipeline_runs(): ...

@pytest.mark.slow
def test_mcmc_convergence(): ...
```

## Writing Unit Tests

Follow the **AAA pattern** (Arrange, Act, Assert). Use class-based grouping:

```python
class TestLmfitParamName:
    """Golden-table tests for lmfit_param_name."""

    @pytest.mark.parametrize(("id_", "field", "expected"), [
        ("p1", "amplitude", "p1_amplitude"),
        ("1",  "center",    "p1_center"),
        ("bg", "slope",     "bg_slope"),
    ])
    def test_golden_table(self, id_: str, field: str, expected: str) -> None:
        assert lmfit_param_name(id_, field) == expected
```

- Use `pytest.fixture()` in `conftest.py` for shared state.
- Use `tmp_path` (built-in pytest fixture) instead of creating local temp files.
- Test file names follow `test_<module_name>.py`.

## Known Exclusions

These tests have pre-existing failures and are excluded from CI:

| Test | Issue |
|------|-------|
| `spectrafit/plugins/test/test_notebook.py::test_solver` | Pydantic SolverAPI errorbars type mismatch (legacy dir) |
| `spectrafit/plugins/test/test_notebook.py::test_generate_report` | Same root cause |

Run with: `uv run pytest spectrafit/ -k "not test_solver and not test_generate_report"` if needed.

## Pre-existing ty Suppressions (Do Not Fix in Unrelated Tasks)

Known ty warnings in frozen or legacy code — do not count against new code.
Type checker: **ty** (hard-fail). mypy has been removed.

- `spectrafit/core/fitting_config.py` — `FitParameter(**constraint)` kwargs mismatch (`missing-argument = "warn"` in `[tool.ty.rules]`)
- `spectrafit/plugins/notebook/core.py` — `GlobalMode` / `SolverModels` argument mismatches (frozen until Phase 6+)

New code must be ty-clean. Add `# type: ignore[<code>]` with a justification comment only for
calls into third-party libraries with incomplete stubs (e.g. lmfit, scipy).

## Integration Test Pattern

```python
@pytest.mark.integration
def test_pipeline_runs_with_config(tmp_path, sample_dataframe):
    cfg = UnifiedFittingConfig(peaks={...}, infile=tmp_path / "data.csv")
    sample_dataframe.to_csv(cfg.infile, index=False)
    pipeline = FittingPipeline(config=cfg)
    result = pipeline.run()
    assert result.result.success
```
