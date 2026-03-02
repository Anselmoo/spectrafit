# Code Style and Conventions

## Formatter / Linter
- **Ruff** (all rules selected, several ignored – see `pyproject.toml`)
  - Google-style docstrings (`pydocstyle.convention = "google"`)
  - Max line / doc length: 100
  - `from __future__ import annotations` required in every module
  - `isort` force-single-line, lines-between-types = 1, lines-after-imports = 2

## Type Hints
- Python 3.10+ syntax: `dict[str, Any]`, `list[str]`, `X | Y` (not `Dict`, `List`, `Optional`)
- Annotated types with `Field()` descriptions in Pydantic models
- `TYPE_CHECKING` guard for heavy imports used only in annotations

## Docstrings
- Google style: `Args:`, `Returns:`, `Raises:`, `Examples:`
- `mkdocs-material` callouts: `!!! note "..."`, `!!! hint "..."`

## Pydantic v2 Patterns
- `model_dump()` (not `.dict()`)
- `model_validate()` (not `parse_obj()`)
- `field_validator` / `model_validator`
- `model_config = ConfigDict(...)` (not `class Config`)
- `Annotated[T, Field(...)]` style preferred

## Error Handling
- Raise typed exceptions (`KeyError`, `ValueError`, `OSError`), NOT `sys.exit()`
- Never use `sys.exit()` in business logic

## Testing
- pytest with markers: `api`, `models`, `unit`, `integration`, `e2e`, `slow`, `validation`
- Notebooks tests: exclude `test_solver` and `test_generate_report` (known Pydantic errorbars type mismatch)

## Prototype Conventions (prototype/ only)
- `ModelInfo` uses `Pydantic BaseModel` with `ConfigDict(frozen=True, arbitrary_types_allowed=True)` — NOT `@dataclass`
- No `from typing import Any`; use `dict[str, object]` for untyped dicts
- `ConfigError(ValueError)` for all config load/parse errors (stores `path` context)
- `typer.echo()` / `typer.style()` instead of `print()`; `typer.Argument`/`typer.Option` for CLI
- Ruff **B008** (`typer.Argument` in defaults) is expected; suppress with `# noqa: B008`
- Ruff **PLC0415** (late imports for circular-import guards) is intentional; suppress with `# noqa: PLC0415`
- Scientific unicode (σ, −) in docstrings is intentional; suppress `RUF001`/`RUF002` per occurrence
- `prototype/` is excluded from the ruff CI scope (`ruff check spectrafit/` only)

## Commit Messages
Conventional Commits with gitmoji:
- `feat: ✨` | `fix: 🐛` | `refactor: ♻️` | `test: ✅` | `docs: 📝` | `chore: 🔨`
