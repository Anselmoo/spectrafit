# Suggested Commands

## Task Runner (poe)
```bash
# All developer workflows via poe (preferred)
uv run poe test          # Run tests/
uv run poe test-fast     # Run tests/ -m 'not slow' -x
uv run poe test-cov      # Run tests/ with coverage term-missing
uv run poe lint          # ruff check + format --check
uv run poe format        # ruff format + ruff check --fix
uv run poe typecheck     # ty check spectrafit/ (warn-only during ty beta)
uv run poe typecheck-legacy  # mypy spectrafit/ (hard-fail fallback)
uv run poe docs-build    # mkdocs build --clean
uv run poe docs-serve    # mkdocs serve
uv run poe ci            # lint + typecheck + test (full local CI pipeline)
uv run poe clean         # remove __pycache__, dist/, coverage artifacts
```

## Testing (direct, if poe unavailable)
```bash
# Run all tests (v2.0.0 suite — fast, skip slow)
uv run pytest tests/ -v

# Run unit tests only
uv run pytest tests/unit/ -v

# Run integration tests
uv run pytest tests/integration/ -v

# Run validation tests
uv run pytest tests/validation/ -v

# Run with coverage (source = spectrafit package)
uv run pytest tests/ --cov=spectrafit --cov-report=xml:coverage.xml -v

# NOTE: Old nested tests in spectrafit/*/test/ are excluded from testpaths.
# To run them explicitly (legacy, may fail due to FittingArgs coupling):
uv run pytest spectrafit/ -v -k "not test_solver and not test_generate_report"
```

## Linting & Formatting (direct)
```bash
uv run ruff check spectrafit/
uv run ruff format spectrafit/
uv run ty check spectrafit/          # type-check (warn-only during beta)
uv run mypy spectrafit/              # type-check (hard-fail, keep until ty matures)
```

## Running the CLI
```bash
uv run spectrafit --help
uv run spectrafit fit --help
uv run spectrafit validate input.toml
```

## Package management
```bash
uv add <package>
uv add <package> --group dev
uv sync --all-groups --all-extras
```

## Package update
```bash
uv lock -U
```

## Prototype (standalone reference in `prototype/`)
```bash
# Generate synthetic CSV data
uv run python prototype/synth_data.py
uv run python prototype/synth_data.py --points 300 --noise gaussian --seed 0

# Run fitting pipeline (outputs prototype/output.json + prototype/fit_plot.png)
uv run python prototype/core_fitting.py prototype/input.toml
uv run python prototype/core_fitting.py prototype/input.toml --show  # display plot

# Ruff check (prototype/ is NOT in CI scope; CI checks spectrafit/ only)
uv run ruff check prototype/
```
