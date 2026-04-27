---
applyTo: "spectrafit/**/*.py,tests/**/*.py"
---

# SpectraFit v1 Legacy Purge Rules

These rules apply to ALL Python files in `spectrafit/` and `tests/`. They document
which patterns are **permanently banned** and what the v2 replacement is.

## Hard-Banned Patterns

| Pattern | Ban Reason | v2 Replacement |
|---------|-----------|---------------|
| `args_out["key"]` | Raw dict crossing module boundary | `FitResult.<property>` |
| `global_: int` | Bare-int mode flag | `FittingMode` StrEnum from `fitting_context.py` |
| New `.from_legacy_dict()` call sites | Bridge only; no new usage | `model_validate()` or `from_dict()` |
| `normalize_unified_config_input()` new callers | Migration adapter | `UnifiedFittingConfig.model_validate()` |
| `SolverModels(df, config)` new instantiation | Legacy shim | `LmfitSolverRuntime(df=df, config=config)` |
| `from typing import Optional` | Python 3.9 syntax | `X | None` |
| `TypeAlias` | Python 3.9 syntax | PEP 695 `type X = ...` |
| `class X(str, Enum)` | Old enum pattern | `class X(StrEnum)` |
| `print()` in `spectrafit/` source | No bare print | `console.print()` (Rich) or `logger` |
| `@property` returning `None` with side-effects | Anti-pattern | Explicit `def method(self) -> None:` |
| `Field(default_factory=dict)` without explicit type | Open schema | Typed Pydantic model |

## Migration Targets (shrink, do not expand)

The following files are **migration targets**. Adding new behavior to them is
forbidden. Any new work that would land here instead belongs in `spectrafit/core/`.

- `spectrafit/models/solver.py` — delegation shim only
- `spectrafit/models/parameter_builder.py` — move to `core/`
- `spectrafit/models/fitting_request.py` — callers should use `UnifiedFittingConfig`
- `spectrafit/report/*` — frozen compat; delegates to `spectrafit/reporting/`
- `spectrafit/jupyter/solver.py` — `@computed_field` FutureWarning shims pending removal

## Allowed Exceptions (comment required)

If a legacy pattern must remain in a bridge/compat file, add a comment:
```python
# intentional: bridge only — <reason>, v2.x migration target
```

Files where exceptions are allowed:
- `spectrafit/report/_compat.py`
- `spectrafit/models/results/fit_result.py` (bridge only)
- `spectrafit/jupyter/solver.py` (FutureWarning shims, scheduled removal)

## Test Legacy Detection

Run this before every PR:
```bash
uv run poe scan-antipatterns
```

Expected output: decreasing finding count over time. Any increase is a regression.
