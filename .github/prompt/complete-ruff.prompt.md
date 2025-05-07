---
mode: "agent"
tools: ["githubRepo", "codebase", "new"]
description: "Complete linting for the provided Python file using ruff in test driven fashon."
---

# Comprehensive Python Code Linting Guide with Ruff

This guide provides a detailed, systematic approach for applying ruff linting to Python code in the SpectraFit project, ensuring code quality while maintaining functionality through test validation.

**Forbidden**: Do not use `cat > /tmp/file.py << 'EOF'`, because this will crash the terminal and Python language server. Multiple lines of code will not be recognized as a single command, leading to syntax errors.
**Better**: Create a new file using `touch /tmp/file.py` or `touch dir/tmp_file.py` and later write into it.

## Overview of Test-Driven Linting

Test-driven linting ensures that code style improvements don't break functionality. This approach requires:

- Running tests after each linting change
- Addressing one category of issues at a time
- Verifying that all tests pass before proceeding to the next issue

## Detailed Linting Workflow

### 1. Initial Assessment

- Run `uv run ruff check spectrafit --statistics` to identify the number and types of issues
- Categorize issues by severity and type (import organization, style, complexity, etc.)
- Plan your approach based on issue distribution

### 2. Code Formatting

- Run `uv run ruff format spectrafit` to automatically fix formatting issues
- Verify formatting with `git diff` to review changes
- Run tests with `uv run pytest tests/<relevant_test_file>.py -v` to confirm no functionality was broken

> This step is crucial as it may resolve many issues automatically, especially those related to style and formatting.

### 3. Automated Fixes

- Apply safe automated fixes: `uv run ruff check spectrafit --fix`
- For more extensive fixes: `uv run ruff check spectrafit --unsafe-fixes`
- Test after each category of fixes: `uv run pytest tests/<relevant_test_file>.py -v`
- Testing is mandatory after each fix to ensure no functionality is broken

### 4. Manual Issue Resolution

- Address remaining issues by category (e.g., `--select E501` for line length issues)
- Example commands:
  - Fix import issues: `uv run ruff check spectrafit --select I --fix`
  - Fix unused variables: `uv run ruff check spectrafit --select F841 --fix`
- Commit changes after each category is resolved and tested
- Testing is mandatory after each fix to ensure no functionality is broken
- Use `--fix` to apply fixes and `--check` to verify changes

### 5. Handling Special Cases

- For issues requiring code restructuring, handle each file individually
- Add targeted exceptions using inline comments: `# noqa: E501` for specific lines
- For file-specific exceptions, update `pyproject.toml` under `tool.ruff.lint.per-file-ignores`

### 6. Final Review

- After all issues are resolved, run `uv run ruff check spectrafit` to ensure no issues remain
- If any issues appears, go back to 1 and repeat the process. It is a cyclic process until all issues are resolved.
- Run all tests to confirm functionality: `uv run pytest tests/`
- Review the code for any remaining style issues

The ruff definitions are defined in `pyproject.toml`.
