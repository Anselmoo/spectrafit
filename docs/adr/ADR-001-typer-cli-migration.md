# ADR-001: Typer CLI Migration

## Status

**Accepted** - Implemented in v1.4.0+

## Context

SpectraFit originally used `argparse` for command-line argument parsing. As the application grew, several issues emerged:

1. **Complexity**: Manual argument parsing and validation logic
2. **Type Safety**: Limited type checking for command-line arguments
3. **User Experience**: No automatic help generation with modern formatting
4. **Maintainability**: Difficult to extend with new commands and options
5. **Testing**: No built-in testing utilities for CLI

## Decision

We decided to migrate from `argparse` to [Typer](https://typer.tiangolo.com/) for CLI implementation.

### Key Benefits

1. **Type Hints**: Leverages Python type hints for automatic validation
2. **Auto-Documentation**: Generates beautiful help text automatically
3. **Subcommands**: Native support for subcommand architecture
4. **Testing**: Built-in `typer.testing.CliRunner` for comprehensive testing
5. **Modern UX**: Intuitive user experience with rich formatting

### Implementation

```python
import typer

app = typer.Typer(
    help="SpectraFit - Fast Fitting Program for ascii txt files.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)

@app.command(name="fit")
def fit(
    infile: Annotated[Path, typer.Argument(...)],
    input: Annotated[Path, typer.Option("-i", "--input", ...)],
) -> None:
    """Fit spectra data using SpectraFit."""
    ...
```

## Consequences

### Positive

- ✅ **Type Safety**: Automatic validation of argument types
- ✅ **Better Testing**: `CliRunner` enables comprehensive CLI tests
- ✅ **Cleaner Code**: Less boilerplate, more readable
- ✅ **Better UX**: Rich help text and error messages
- ✅ **Extensibility**: Easy to add new commands

### Negative

- ⚠️ **Breaking Change**: Users must update scripts using old CLI
- ⚠️ **Migration Effort**: Required updating all CLI code
- ⚠️ **New Dependency**: Added `typer` as a core dependency

### Neutral

- 📝 **Learning Curve**: Team needs to learn Typer patterns
- 📝 **Documentation**: All CLI documentation needed updates

## Alternatives Considered

### 1. Click

**Pros**: Mature, widely used, battle-tested
**Cons**: More verbose than Typer, less type-safe

### 2. Fire

**Pros**: Minimal boilerplate
**Cons**: Limited validation, unclear error messages

### 3. argparse (Status Quo)

**Pros**: Standard library, no dependencies
**Cons**: Verbose, limited features, no type safety

## Related Decisions

- ADR-002: Plugin Architecture (depends on Typer subcommands)
- ADR-003: Subcommand Structure (enabled by Typer)

## References

- [Typer Documentation](https://typer.tiangolo.com/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [SpectraFit Issue #XXX](https://github.com/Anselmoo/spectrafit/issues/)

## Revision History

| Date       | Version | Author       | Description           |
| ---------- | ------- | ------------ | --------------------- |
| 2025-01-15 | 1.0     | Copilot Team | Initial ADR creation  |
