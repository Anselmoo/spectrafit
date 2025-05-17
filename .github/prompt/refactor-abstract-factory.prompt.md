---
mode: "agent"
tools: ["githubRepo", "codebase"]
description: "Refactor the provided Python file to apply the Abstract Factory and Facade design patterns."
---

# Abstract Factory & Facade Pattern Refactoring for SpectraFit

## Overview

This prompt guides the refactoring of the complete SpectraFit codebase to implement the Abstract Factory design pattern for internal extensibility and the Facade pattern for a simplified user-facing API. This hybrid approach will organize the creation of families of related objects in the spectral analysis domain, improve maintainability, and provide a clear, unified interface for end users.

## Goals

- Refactor the SpectraFit codebase to use Abstract Factory patterns for related object families (e.g., models, analyzers, converters, visualization tools)
- Introduce a Facade layer to expose a unified, user-friendly API that delegates to the underlying factories and products
- Ensure all implementations adhere to the Dependency Inversion Principle
- Maintain backwards compatibility with existing client code
- Improve type safety and validation using pydantic models
- Create clear separation between abstract interfaces, concrete implementations, and the Facade

## Implementation Requirements

1. Define abstract factory interfaces for each family of related components
2. Create concrete factory implementations for specific use cases (e.g., different spectroscopy techniques)
3. Refactor client code to depend on abstractions rather than concrete classes
4. Update all model creation logic to use factory methods instead of direct instantiation
5. Implement a Facade class that provides a simplified API for common SpectraFit workflows, delegating to the factories
6. Ensure all new code passes quality checks with ruff, mypy (strict mode), and pytest

## Testing Requirements

- Implement comprehensive unit tests for all new abstract factories, their products, and the Facade
- Update existing tests to work with the new architecture
- Maintain or improve current test coverage (verify with pytest --cov)
- Ensure type safety with mypy --strict
- Validate code quality with ruff

## Reference

For implementation guidance, refer to:

- https://github.com/faif/python-patterns/blob/master/patterns/creational/abstract_factory.py
- https://github.com/faif/python-patterns/blob/master/patterns/structural/facade.py
- The existing API structure in spectrafit.api modules
