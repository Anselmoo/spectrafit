# Task Completion Checklist

When a coding task is done:

1. **Format** – `uv run ruff format spectrafit/`
2. **Lint** – `uv run ruff check spectrafit/` (auto-fix is on)
3. **Type-check** – `uv run mypy spectrafit/`
4. **Test** – `uv run pytest tests/ -v` (active suite; legacy `spectrafit/*/test/` is excluded)
5. **Commit** – follow Conventional Commits + gitmoji (see code_style_and_conventions.md)

## Notes
- Do NOT fix unrelated pre-existing failures.
- Known failures to skip (legacy dirs only, not in active suite): `test_solver`, `test_generate_report` in `plugins/test/test_notebook.py`.
- **Pre-existing mypy errors (5)** in `spectrafit/core/fitting_config.py` (FitParameter **kwargs) and `spectrafit/plugins/notebook/core.py` (GlobalMode int cast, SolverModels args kwarg). Do NOT fix as part of unrelated tasks.
- All new code must have Google-style docstrings and type hints.
- Use `Annotated[T, Field(...)]` in Pydantic models.
