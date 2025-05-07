---
mode: "agent"
tools: ["githubRepo", "codebase", "new"]
description: "Complete unit-tests via pytest including coverage"
---

# Complete the unit-tests for the provided Python file using pytest and ensure coverage.

## First Step:

- Run pytest step by step with `uv run pytest spectrafit/<test_file> -v` to see the test results.
- Check the coverage file based on the test results.
- Complete missing parts of the code to ensure all tests pass.
- Fix failed tests and ensure all tests pass.
- Ensure the code is clean and follows best practices.
- Make use of `conftest.py` for shared fixtures and configurations.
- Make use of decorators for test functions to avoid code duplication.
- Try to avoid local test files and use tmp files instead.
- Use markers in `[tool.pytest.ini_options]` in `pyproject.toml` to categorize tests.

## Final Step:

- Run pytest with `--cov` to check the coverage.
- Compare the coverage report with the previous one.
- Add more test and start with **First Step:**

## Important Rules:

- Do not perform equality checks with floating point values. --> Use `np.isclose()` or `pytest.approx()`.

## Optional:

- End2end tests should be in a separate file.
- Benchmark tests should be in a separate file.
- Performance tests should be in a separate file.
- Use `tox`.
- Use `pytest-benchmark` for performance tests.
