---
applyTo: "**/*.py"
---

# Project coding standards for Python

## General Package Management

- Use `uv` for package management.
  - Test with `uv run pytest <test_file.py> -v` and `uv run <script.py>`.
  - Add packages with `uv add <package_name>` and for development with `uv add <package_name> --group dev`.
- Define all dependencies in `pyproject.toml`.
- Define all settings in `pyproject.toml`.

## General Style

- Follow `RUFF` guidelines, but many arguments in function definitions can be partially omitted.
- Use type hints for python 3.8+.
- Prefer explicit over implicit code.
- Use descriptive variable names.
- Keep functions small and focused.
- Prefer `pydantic` for data validation and settings management over `dataclasses` and `NamedTuple`.

## Documentation Conventions

- Use Google style docstrings.
- Use `Args` and `Returns` sections in docstrings.
- Use `Raises` section for exceptions.
- Use `Examples` section for usage examples.
- Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) and [mkdocs-material](https://squidfunk.github.io/mkdocs-material/) for docstrings.
- Used mkdocs-material annotations like `!!! info "<Topic>"` for documentation.

## Error Handling

- Handle NaN and invalid values gracefully, using `np.nan_to_num` or similar.
- Provide informative error messages.
- Use `raise` conditionals for errors.
