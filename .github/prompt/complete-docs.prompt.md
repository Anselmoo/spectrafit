---
mode: "agent"
tools: ["githubRepo", "codebase", "#new"]
description: "Refactor the provided Python file to apply the Abstract Factory design pattern."
---

- Complete the documentation for the provided [Python](spectrafit/) file and [markdown files](docs/).
- Use the [documentation standards](.github/instructions/doc-coding.instructions.md) as a guide.
- Use the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) and [mkdocs-material](https://squidfunk.github.io/mkdocs-material/) for docstrings.
- Also update the corresponding `mkdocs.yml` file to include the new documentation.

- Refactor missing type definitions in the documentation. For example:

  ```python
  def add(a: int, b: int = 0) -> int:
  """Add two numbers together.

  Args:
      a: The first number.
      b: The second number.
  Returns:
      The sum of the two numbers.
  """
      return a + b
  ```

  should be updated to:

  ```python
  def add(a: int, b: int) -> int:
  """Add two numbers together.

  Args:
      a (int): The first number.
      b (int, optional): The second number. Defaults to 0.
  Returns:
      int: The sum of the two numbers.
  """
      return a + b
  ```
