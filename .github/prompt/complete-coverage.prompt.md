---
mode: "agent"
tools: ["githubRepo", "codebase", "new"]
description: "Iteratively complete unit-tests for exclusive coverage using pytest and JSON coverage reports."
---

# Iterative Coverage-Driven Unit Test Completion

## Workflow

1. **Run Coverage-Exclusive Tests:**

   - Use the following command to run tests and generate a JSON coverage report:
     ```shell
     python tools/analyze_coverage.py
     ```
   - After the big test run, use:
     ```shell
     uv run pytest spectrafit/<test-folder> --cov=./spectrafit/<test-folder> --cov-report=json:test_fodler_coverage.json
     ```
     This will allow to run more specific tests in the `spectrafit/<test-folder>` folder and faster incremental tests coverage.
   - This will output coverage data to `coverage.json`.

2. **Analyze Coverage:**

   - Parse `coverage.json` to identify which lines, functions, or files are not covered by tests.
   - Focus only on code that is not yet covered (exclusive coverage approach).

3. **Iterative Test Extension:**

   - For each uncovered code region:
     - Write or extend tests in `spectrafit/` (or its test subfolders) to cover the missing logic.
     - Use fixtures and decorators from `conftest.py` for shared setup.
     - Prefer temporary files over local test files.
     - Use `[tool.pytest.ini_options]` markers in `pyproject.toml` for test categorization.
   - Do not perform equality checks with floating point values; use `np.isclose()` or `pytest.approx()`.

4. **Repeat:**

   - Re-run the coverage command after each test addition or fix.
   - Continue until all relevant code is covered or justified as untestable.

5. **Finalization:**
   - When coverage is satisfactory, compare the new `coverage.json` with previous reports to confirm improvement.
   - Optionally, separate end-to-end, benchmark, and performance tests into their own files.

## Notes

- This process is iterative and coverage-driven: always use the latest `coverage.json` as the input for the next test-writing step.
- The goal is to maximize coverage in an efficient, targeted manner, not to re-test already-covered code.
- Use `tox` or `pytest-benchmark` for advanced scenarios if needed.
