---
mode: "agent"
tools: ["githubRepo", "codebase"]
description: "Refactor SpectraFit codebase to implement Abstract Factory and Facade design patterns in a coordinated hybrid approach."
---

# Abstract Factory & Facade Hybrid Pattern Refactoring for SpectraFit

## Overview

This prompt guides the refactoring of the complete SpectraFit codebase to implement a **hybrid architecture** combining:

1. **Abstract Factory Pattern** for internal extensibility - organizing the creation of families of related objects (models, analyzers, solvers)
2. **Facade Pattern** for simplified user experience - providing unified, high-level interfaces that delegate to the factory-created components

This coordinated approach will organize object creation in the spectral analysis domain, improve maintainability, and provide clear separation between internal complexity and user-facing simplicity.

## Architecture Integration

### Hybrid Pattern Relationship

- **Abstract Factory** creates families of related components internally
- **Facade** provides simplified interfaces that use factory-created objects
- **Integration Point**: Facades delegate to factories, not direct instantiation

### Component Families (Abstract Factory)

- **Model Family**: Peak models (Gaussian, Lorentzian, PseudoVoigt), background models (Linear, Polynomial)
- **Analyzer Family**: Statistical analyzers, correlation analyzers, residual analyzers
- **Solver Family**: Optimization engines, minimizers, constraint handlers
- **I/O Family**: Data loaders (CSV, JSON, YAML), validators, converters

### Facade Interfaces

- **Primary Facade**: `SpectraFitFacade` - Complete workflow orchestration
- **Specialized Facades**: `FittingFacade`, `AnalysisFacade` - Domain-specific operations
- **Legacy Facade**: `LegacyAPIFacade` - Backward compatibility layer

## Goals

- Implement Abstract Factory patterns for related object families using dependency injection
- Create Facade layer that delegates to factory-created components
- Ensure all implementations adhere to the Dependency Inversion Principle
- Maintain backwards compatibility with existing client code
- Improve type safety and validation using pydantic models
- Create clear separation between abstract interfaces, concrete implementations, and user-facing APIs

## Implementation Sequence

1. **Phase 1**: Create abstract interfaces and factory foundations
2. **Phase 2**: Implement concrete factories and refactor existing models
3. **Phase 3**: Build facade layer that uses factories
4. **Phase 4**: Integrate facades with existing CLI and API
5. **Phase 5**: Testing, documentation, and migration support

## Implementation Requirements

### Abstract Factory Implementation

1. Define abstract factory interfaces for each component family in `spectrafit/interfaces/`
2. Create concrete factory implementations for specific use cases in `spectrafit/factories/`
3. Implement factory registry system for managing different factory types
4. Update all object creation logic to use factory methods instead of direct instantiation

### Facade Implementation

5. Implement core `SpectraFitFacade` that orchestrates complete workflows using factory-created components
6. Create specialized facades for specific use cases (`FittingFacade`, `AnalysisFacade`)
7. Build legacy compatibility facade to maintain existing API behavior
8. Integrate facades with existing CLI and plugin systems

### Quality and Integration

9. Ensure all new code passes quality checks with ruff, mypy (strict mode), and pytest
10. Refactor client code to depend on abstractions rather than concrete classes
11. Maintain full backward compatibility for existing API consumers
12. Implement comprehensive error handling and validation

## Testing Requirements

### Factory Testing

- Implement comprehensive unit tests for all abstract factories and their concrete implementations
- Test factory registry system and factory discovery mechanisms
- Validate parameter handling and model creation across all factory types

### Facade Testing

- Test complete workflow orchestration through facade interfaces
- Verify facade delegation to factory-created components
- Test error handling and edge cases in simplified APIs

### Integration Testing

- Update existing tests to work with the new factory-based architecture
- Test backward compatibility with existing API usage patterns
- Maintain or improve current test coverage (verify with `pytest --cov`)
- Ensure type safety with `mypy --strict`
- Validate code quality with `ruff`

### Performance Testing

- Benchmark factory creation vs direct instantiation overhead
- Test memory usage patterns with factory caching strategies
- Validate that facade layers don't introduce significant performance penalties

## Reference

For detailed implementation guidance, refer to:

- [Abstract Factory Pattern Implementation](../instructions/architecture-refactoring-abstract-factory.instructions.md)
- [Facade Pattern Implementation](../instructions/architecture-refactoring-facade.instructions.md)
- [Python Patterns - Abstract Factory](https://github.com/faif/python-patterns/blob/master/patterns/creational/abstract_factory.py)
- [Python Patterns - Facade](https://github.com/faif/python-patterns/blob/master/patterns/structural/facade.py)
- [SpectraFit API Documentation](../../docs/api/) for existing architecture context

## Success Criteria

- [ ] All existing functionality accessible through both new facades and legacy APIs
- [ ] Factory system supports easy addition of new model types without breaking changes
- [ ] Code complexity reduced for end users while maintaining full feature access
- [ ] All tests pass with improved or maintained coverage
- [ ] Type safety validated with mypy --strict
- [ ] Performance impact minimal (<5% overhead for common operations)
- [ ] Documentation updated with migration examples and new usage patterns
