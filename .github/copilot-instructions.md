# Copilot Instructions for SpectraFit

To ensure consistent, maintainable, and high-quality code suggestions for the SpectraFit project, follow these guidelines:

---

## Project Structure

- Place new code in the most appropriate module or submodule (e.g., `models.py`, `plotting.py`, `report.py`, `tools.py`, `api/`, `plugins/`, `test/`).
- Keep test code in the `test/` subfolders and use `pytest`.

## Data Handling

- Input files: Support JSON, YAML, and TOML. Input must define initial peak parameters.
- Output files: Support CSV and JSON.
- Use the existing data model and serialization patterns.

## Parameter and Model Consistency

- Use the parameter conventions and nested structure as shown in the input files and `/docs/interface/usage.md`.
- Example peak definition:
- ```json
  "peaks": {
    "1": {
      "pseudovoigt": {
        "amplitude": { "max": 2, "min": 0, "vary": true, "value": 1 },
        "center":    { "max": 2, "min": -2, "vary": true, "value": 0 },
        "fwhmg":     { "max": 0.1, "min": 0.02, "vary": true, "value": 0.01 },
        "fwhml":     { "max": 0.1, "min": 0.01, "vary": true, "value": 0.01 }
      }
    }
  }
  ```

## Minimizer and Optimizer Settings

- Always include and respect `minimizer` and `optimizer` settings in fitting routines.
- Example:
  ```json
  "minimizer": { "nan_policy": "propagate", "calc_covar": true },
  "optimizer": { "max_nfev": 1000, "method": "leastsq" }
  ```

## Reporting and Statistics

- Use the existing reporting structure for fit statistics, confidence intervals, and variable analysis.
- Output should be compatible with pandas DataFrames when possible.

## Error Handling

- Handle NaN and invalid values gracefully, using `np.nan_to_num` or similar.
- Provide informative error messages.

## Command Line Interface

- CLI arguments must be overridable by input file settings and vice versa, as described in `/docs/interface/usage.md`.

## Documentation

- Add or update docstrings and reference `/docs/` for user-facing documentation.
- Keep code and documentation in sync.

## General Style

- Follow PEP8.
- Use type hints.
- Prefer explicit over implicit code.
- Use descriptive variable names.
- Keep functions small and focused.

---

## Conventional Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages.
- Use the [VSCode Conventional Commits](https://github.com/vivaxy/vscode-conventional-commits) emoji, respectively, gitmoji type style for commit messages:

| Type     |            Emoji             | Description                         |
| -------- | :--------------------------: | ----------------------------------- |
| feat     |      `:sparkles:` (✨)       | A new feature                       |
| fix      |         `:bug:` (🐛)         | A bug fix                           |
| docs     |        `:memo:` (📝)         | Documentation only changes          |
| style    |      `:lipstick:` (💄)       | Changes that do not affect meaning  |
| refactor |       `:recycle:` (♻️)       | Code change that is not a fix/feat  |
| perf     |         `:zap:` (⚡)         | Performance improvement             |
| test     |  `:white_check_mark:` (✅)   | Adding or correcting tests          |
| build    | `:construction_worker:` (👷) | Build system or dependencies        |
| ci       |       `:wrench:` (🔧)        | CI/CD configuration                 |
| chore    |       `:hammer:` (🔨)        | Other changes that don't modify src |
| revert   |       `:rewind:` (⏪)        | Reverts a previous commit           |

**Example commit messages:**

```text
feat: ✨ add new peak fitting method
fix: 🐛 handle NaN values in solver
docs: 📝 update usage documentation
test: ✅ add regression test for optimizer
refactor: ♻️ merge dictionary assignments in report generation
chore: 🔨 update dependencies
```

---

## Branching Rules (Trunk-Based Development)

- All changes should branch from `main`.
- Use short-lived feature branches named with the pattern:
  `type/short-description`
  Examples:
  - `feat/peak-fitting`
  - `fix/nan-handling`
  - `docs/usage-update`
- Merge to `main` via pull request after review and passing CI.
- Rebase frequently to keep branches up to date with `main`.
- Delete feature branches after merge.
