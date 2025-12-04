# ADR-003: Subcommand Structure

## Status

**Accepted** - Implemented in v2.0.0

## Context

The original SpectraFit CLI had a monolithic command structure:

```bash
spectrafit <infile> -i <input.toml> [options...]
```

This approach had several issues:

1. **Single Entry Point**: All functionality through one command
2. **Option Overload**: Too many flags and options
3. **Unclear Purpose**: Hard to discover different features
4. **No Grouping**: Related operations not organized
5. **Extension Difficulty**: Adding new features cluttered the interface

## Decision

We restructured the CLI into a **hierarchical subcommand architecture**:

```bash
spectrafit <command> [subcommand] [arguments] [options]
```

### Command Hierarchy

```
spectrafit
├── fit                 # Core fitting functionality
├── validate           # Validate configuration files
├── convert            # Convert between file formats
├── report             # Generate fitting reports
└── plugins            # Plugin management and commands
    ├── list          # List available plugins
    ├── rixs          # RIXS visualizer
    ├── jupyter       # Jupyter integration
    └── moessbauer-info  # Mössbauer information
```

### Implementation

```python
# Main app
app = typer.Typer(
    help="SpectraFit - Fast Fitting Program for ascii txt files.",
    no_args_is_help=True,
)

# Register subcommands
app.command(name="fit")(fit)
app.command(name="validate")(validate)
app.command(name="convert")(convert)
app.command(name="report")(report)

# Register plugin subcommand group
app.add_typer(plugins_app, name="plugins")
```

## Consequences

### Positive

- ✅ **Discoverability**: Clear command structure
- ✅ **Organization**: Related commands grouped together
- ✅ **Scalability**: Easy to add new commands
- ✅ **Help System**: Hierarchical help with `--help` at each level
- ✅ **Separation**: Core vs. plugin features clearly separated
- ✅ **Plugin Integration**: Natural place for plugin commands

### Negative

- ⚠️ **Breaking Change**: Old CLI syntax no longer works
- ⚠️ **Migration**: Users must update scripts and documentation
- ⚠️ **Verbosity**: More typing for simple operations

### Neutral

- 📝 **Learning Curve**: Users need to learn new command structure
- 📝 **Documentation**: Complete CLI documentation rewrite needed

## Command Design Principles

### 1. Clear Naming

Commands should use clear, descriptive verbs:
- `fit` - perform fitting
- `validate` - validate configuration
- `convert` - convert file formats
- `report` - generate reports

### 2. Consistent Options

Common options use consistent names:
- `-i`, `--input` - input configuration file
- `-o`, `--output` - output file/directory
- `-v`, `--verbose` - verbosity level
- `-h`, `--help` - show help

### 3. Help at Every Level

```bash
spectrafit --help                    # Main help
spectrafit fit --help                # Fit command help
spectrafit plugins --help            # Plugins help
spectrafit plugins rixs --help       # RIXS plugin help
```

### 4. Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid usage (missing arguments, etc.)

## Usage Examples

### Core Fitting

```bash
# Old (deprecated)
spectrafit data.csv -i input.toml -o results/

# New
spectrafit fit data.csv -i input.toml -o results/
```

### Validation

```bash
spectrafit validate input.toml
```

### Conversion

```bash
spectrafit convert input.json -o output.toml
```

### Plugin Commands

```bash
# List available plugins
spectrafit plugins list

# Use RIXS visualizer
spectrafit plugins rixs data.npz -p 8080

# Show Mössbauer info
spectrafit plugins moessbauer-info
```

## Backward Compatibility

To ease migration, we maintain compatibility:

1. **Legacy Entry Points**: Old standalone commands still work
   ```bash
   spectrafit-rixs-visualizer data.npz  # Still works
   spectrafit plugins rixs data.npz     # New way
   ```

2. **Migration Guide**: Documentation for updating scripts

3. **Deprecation Warnings**: (Future) Warn about old command usage

## Command Responsibilities

### `fit`

- Load data and configuration
- Perform spectral fitting
- Generate results and plots
- Save output files

### `validate`

- Check configuration file syntax
- Validate parameter ranges
- Verify model definitions
- Report configuration issues

### `convert`

- Convert between JSON, TOML, YAML formats
- Preserve all configuration data
- Validate on conversion

### `report`

- Generate fitting reports
- Create visualizations
- Export to various formats (CSV, JSON, PDF)

### `plugins`

- List available plugins
- Access plugin-specific commands
- Manage plugin discovery

## Alternatives Considered

### 1. Keep Monolithic CLI

**Pros**: No breaking changes, simpler structure
**Cons**: Scalability issues, poor UX, hard to extend

### 2. Separate Executables

**Pros**: Clear separation
**Cons**: Installation complexity, no unified interface

### 3. Config-Based Dispatch

**Pros**: Flexible
**Cons**: Hidden functionality, poor discoverability

## Testing Strategy

Each command level has dedicated tests:

```python
from typer.testing import CliRunner

def test_fit_command():
    result = runner.invoke(app, ["fit", "data.csv", "-i", "input.toml"])
    assert result.exit_code == 0

def test_plugins_list():
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0
    assert "rixs" in result.output
```

## Related Decisions

- ADR-001: Typer CLI Migration (enables subcommands)
- ADR-002: Plugin Architecture (plugins as subcommands)

## References

- [Typer Subcommands](https://typer.tiangolo.com/tutorial/subcommands/)
- [Git CLI Structure](https://git-scm.com/docs) (inspiration)
- [Click Nested Commands](https://click.palletsprojects.com/en/8.1.x/commands/)

## Revision History

| Date       | Version | Author       | Description          |
| ---------- | ------- | ------------ | -------------------- |
| 2025-01-15 | 1.0     | Copilot Team | Initial ADR creation |
