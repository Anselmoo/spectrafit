---
mode: "agent"
tools: ["githubRepo", "codebase", "new"]
description: "Complete type checking for the provided Python file using mypy in test driven fashion."
---

# Comprehensive Python Type Checking Guide with MyPy

This guide provides a detailed, systematic approach for applying mypy type checking to Python code in the SpectraFit project, ensuring type safety while maintaining functionality through test validation.

**Forbidden**: Do not use `cat > /tmp/file.py << 'EOF'`, because this will crash the terminal and Python language server. Multiple lines of code will not be recognized as a single command, leading to syntax errors.
**Better**: Create a new file using `touch /tmp/file.py` or `touch dir/tmp_file.py` and later write into it.

## Overview of Test-Driven Type Checking

Test-driven type checking ensures that adding type annotations doesn't break functionality. This approach requires:

- Running tests after adding or modifying type annotations
- Addressing one module or component at a time
- Verifying that all tests pass before proceeding to the next component

## Detailed Type Checking Workflow

### 1. Initial Assessment

- Run `uv run mypy spectrafit/**/*.py --pretty` to identify the number and types of type issues
- Categorize issues by severity and type (missing annotations, incompatible types, etc.)
- Plan your approach based on issue distribution

### 2. Importing Type Annotations

- Begin by adding imports needed for type hints:
  ```python
  from typing import Dict, List, Optional, Tuple, Union, Any, Callable
  ```
- For Python 3.9+, consider using built-in generics:
  ```python
  dict[str, int]  # Instead of Dict[str, int]
  ```

### 3. Incremental Type Annotation

- Start with function signatures, then move to variable annotations
- Example approach:
  - Add return type annotations: `def function() -> ReturnType:`
  - Add parameter type annotations: `def function(param: ParamType) -> ReturnType:`
  - Add variable annotations: `variable: Type = value`
- Test after each module: `uv run pytest tests/<relevant_test_file>.py -v`
- Testing is mandatory after each set of annotations to ensure no functionality is broken

### 4. Complex Type Handling

- Use Union types for variables that could be multiple types: `Union[str, int]` or `str | int` (Python 3.10+)
- Use Optional for values that might be None: `Optional[str]` or `str | None` (Python 3.10+)
- For collections with mixed types, consider:

  ```python
  from typing import TypedDict

  class ConfigDict(TypedDict):
      name: str
      value: float
      enabled: bool
  ```

- For complex return types, use type aliases:

  ```python
  ResultType = Tuple[np.ndarray, Dict[str, float]]

  def analyze_data() -> ResultType:
      # ...
  ```

### 5. Handling Special Cases

- For dynamically generated attributes, use:

  ```python
  class Model:
      def __init__(self) -> None:
          pass

      def __setattr__(self, name: str, value: Any) -> None:
          # Dynamic attribute setting
          super().__setattr__(name, value)
  ```

- For third-party libraries without type stubs, use:
  ```python
  import untyped_library  # type: ignore
  ```
- Add targeted exceptions using inline comments: `# type: ignore` for specific lines
- For file-specific exceptions, update `pyproject.toml` under `tool.mypy`

### 6. Addressing Error Suppression

- Avoid using blanket `# type: ignore` without comments
- Use more specific ignore comments: `# type: ignore[attr-defined]`
- Document reasons for type ignores:
  ```python
  result = complex_function()  # type: ignore[no-any-return]  # API returns dynamic structure
  ```

### 7. Utilizing Type Checking in Integrated Tests

- Create tests that verify expected behavior with type annotations:
  ```python
  def test_annotations_dont_affect_behavior() -> None:
      # Test function with type annotations
      assert function(param=1) == expected_result
  ```

### 8. Important Type Definitions

- Prefer `RUF012` for `typing.ClassVar` over mypy's `ClassVar` definition

### 9. Final Review

- After all issues are resolved, run `uv run mypy spectrafit` to ensure no issues remain
- If any issues appear, go back to step 1 and repeat the process. It is a cyclic process until all issues are resolved.
- Run all tests to confirm functionality: `uv run pytest tests/`
- Review the annotations for consistency and completeness

The mypy configurations are defined in [`mypy.ini`](./mypy.ini).
