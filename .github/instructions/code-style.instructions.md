---
applyTo: "spectrafit/**/*.py,tests/**/*.py,prototype/**/*.py"
---

# SpectraFit Code Style & Conventions

## Module Header

Every Python module must begin with:

```python
"""Module docstring."""

from __future__ import annotations
```

The `from __future__ import annotations` import is **required** in every module.

## Formatter / Linter

- **Ruff** is the formatter and linter. Run `uv run ruff format spectrafit/` then `uv run ruff check spectrafit/`.
- Max line length: **100 characters**. Max docstring length: **100 characters**.
- `isort` settings: `force-single-line`, `lines-between-types = 1`, `lines-after-imports = 2`.
- `pydocstyle.convention = "google"` — Google-style docstrings throughout.
- CI scope: `ruff check spectrafit/` (not `prototype/`; that is a separate sandbox).

## Approved `# noqa` Suppressions

| Suppression | Reason |
|-------------|--------|
| `# noqa: B008` | `typer.Argument`/`typer.Option` in default parameter values — expected pattern |
| `# noqa: PLC0415` | Late imports for circular-import guards — intentional |
| `# noqa: RUF001` / `# noqa: RUF002` | Scientific Unicode (σ, −, ×) in docstrings |

## Type Hints

- Use Python 3.12+ syntax: `dict[str, Any]`, `list[str]`, `X | Y` (never `Dict`, `List`, `Optional`).
- Use `TYPE_CHECKING` guard for heavy imports used only in annotations:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
```

- Use the PEP 695 `type` keyword for all type aliases (Python 3.12+):

```python
# Python 3.12+ — use PEP 695 type keyword
type JsonValue = float | int | str | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
```

- Use `StrEnum` (not `class X(str, Enum)`) for string enumerations.
- No bare `from typing import Any` in new code; use `dict[str, object]` for truly untyped dicts
  where possible.

## Docstrings (Google Style)

```python
def my_function(x: float, y: str) -> bool:
    """One-line summary.

    Extended description paragraph (optional).

    Args:
        x: Description of x.
        y: Description of y.

    Returns:
        Description of return value.

    Raises:
        ValueError: When x is negative.

    Examples:
        >>> my_function(1.0, "hello")
        True
    """
```

Use `mkdocs-material` callouts in module/class docstrings: `!!! note "..."`, `!!! hint "..."`.

## Pydantic v2 Patterns

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Annotated

class MyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: Annotated[float, Field(ge=0.0, description="Non-negative value")]
    name: Annotated[str, Field(min_length=1, description="Component name")]

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()
```

- Always `model_dump()` (not `.dict()`), `model_validate()` (not `parse_obj()`).
- `Annotated[T, Field(...)]` style is preferred over `Field()` as default value.
- `model_config = ConfigDict(...)` (not inner `class Config`).

## Error Handling

- Raise typed exceptions: `KeyError`, `ValueError`, `OSError`, `ConfigError`.
- **Never** `sys.exit()` in business logic — only in CLI entry points.
- Use `ConfigError(ValueError)` (from `spectrafit/models/peak_models.py`) for config
  parse/validation errors; store `path` context for actionable diagnostics.

## CLI Patterns (Typer)

```python
import typer

app = typer.Typer(help="...", no_args_is_help=True)

@app.command()
def run(
    infile: Path = typer.Argument(..., help="Input file"),  # noqa: B008
    verbose: bool = typer.Option(False, "--verbose", "-v"),  # noqa: B008
) -> None:
    typer.echo(typer.style("✓ Done", fg=typer.colors.GREEN))
```

Use `typer.echo()` / `typer.style()` instead of `print()`.

## Commit Messages

Follow Conventional Commits + gitmoji:

| Type | Emoji | Example |
|------|-------|---------|
| `feat` | ✨ | `feat: ✨ add BatchFittingConfig for parallel multi-spectrum fits` |
| `fix` | 🐛 | `fix: 🐛 correct lmfit_param_name for numeric ids` |
| `refactor` | ♻️ | `refactor: ♻️ replace define_parameters* with build_composite_model` |
| `test` | ✅ | `test: ✅ add golden-table tests for translate_dot_notation` |
| `docs` | 📝 | `docs: 📝 update architecture.instructions.md for v2 wiring` |
| `chore` | 🔨 | `chore: 🔨 remove spectrafit.py legacy shim` |

Co-authored-by trailer is always required:
```
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```
