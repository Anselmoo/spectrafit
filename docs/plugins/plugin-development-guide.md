# Plugin Development Guide

This guide explains how to create plugins for SpectraFit.

## Overview

SpectraFit uses a plugin architecture that allows you to extend its functionality with custom commands and models. Plugins are discovered automatically using Python entry points.

## Plugin Protocol

All plugins must implement the `SpectraFitPlugin` protocol:

```python
from typing import Protocol
import typer

class SpectraFitPlugin(Protocol):
    """Protocol for SpectraFit plugins."""

    name: str                    # Unique plugin identifier
    version: str                 # Semantic version (e.g., "1.0.0")
    description: str             # Short description

    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register CLI commands with the parent Typer app."""
        ...

    def register_models(self) -> list[type]:
        """Return list of Pydantic models this plugin provides."""
        ...
```

## Creating a Plugin

### Step 1: Create Plugin Class

Create a new Python file for your plugin (e.g., `my_plugin.py`):

```python
"""My custom SpectraFit plugin."""

from __future__ import annotations

from typing import Annotated
import typer
from spectrafit.plugins.protocol import SpectraFitPlugin


class MyPlugin:
    """My custom plugin for SpectraFit."""

    name = "my-plugin"
    version = "1.0.0"
    description = "A custom plugin that does amazing things"

    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register plugin commands."""

        @parent_app.command(name="my-command")
        def my_command(
            input_file: Annotated[
                str,
                typer.Argument(help="Input file path"),
            ],
            option: Annotated[
                str,
                typer.Option("-o", "--option", help="Custom option"),
            ] = "default",
        ) -> None:
            """My custom command that processes files."""
            typer.echo(f"Processing {input_file} with option={option}")
            # Your plugin logic here

    def register_models(self) -> list[type]:
        """Register Pydantic models used by this plugin."""
        # Return any Pydantic models your plugin provides
        return []


# Verify protocol implementation
assert isinstance(MyPlugin(), SpectraFitPlugin)
```

### Step 2: Add Entry Point

In your `pyproject.toml`, add an entry point:

```toml
[project.entry-points."spectrafit.plugins"]
my-plugin = "my_package.my_plugin:MyPlugin"
```

### Step 3: Install and Test

Install your plugin package:

```bash
pip install -e .
```

Verify your plugin is discovered:

```bash
spectrafit plugins list
```

Use your plugin:

```bash
spectrafit plugins my-command input.txt -o custom
```

## Plugin Examples

### Example 1: Data Export Plugin

```python
"""Export plugin for additional file formats."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from spectrafit.plugins.protocol import SpectraFitPlugin


class ExportPlugin:
    """Plugin for exporting data to various formats."""

    name = "export"
    version = "1.0.0"
    description = "Export fitting results to additional formats"

    def register_commands(self, parent_app: typer.Typer) -> None:
        @parent_app.command(name="export-excel")
        def export_excel(
            infile: Annotated[
                Path,
                typer.Argument(help="Input CSV file from fitting"),
            ],
            outfile: Annotated[
                Path,
                typer.Option("-o", "--output", help="Output Excel file"),
            ] = Path("output.xlsx"),
        ) -> None:
            """Export fitting results to Excel format."""
            import pandas as pd

            df = pd.read_csv(infile)
            df.to_excel(outfile, index=False)
            typer.echo(f"✅ Exported to {outfile}")

    def register_models(self) -> list[type]:
        return []
```

### Example 2: Validation Plugin

```python
"""Validation plugin for custom model checking."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel, Field
from spectrafit.plugins.protocol import SpectraFitPlugin


class CustomValidationModel(BaseModel):
    """Custom validation rules."""

    max_peaks: int = Field(ge=1, le=100)
    min_amplitude: float = Field(ge=0.0)


class ValidationPlugin:
    """Plugin for custom validation rules."""

    name = "custom-validation"
    version = "1.0.0"
    description = "Apply custom validation rules to configurations"

    def register_commands(self, parent_app: typer.Typer) -> None:
        @parent_app.command(name="validate-custom")
        def validate_custom(
            config_file: Annotated[
                Path,
                typer.Argument(help="Configuration file to validate"),
            ],
        ) -> None:
            """Validate configuration with custom rules."""
            # Load and validate configuration
            typer.echo(f"Validating {config_file}...")
            # Your validation logic here
            typer.echo("✅ Validation passed!")

    def register_models(self) -> list[type]:
        return [CustomValidationModel]
```

### Example 3: Analysis Plugin

```python
"""Analysis plugin for statistical analysis."""

from __future__ import annotations

from typing import Annotated

import typer
from spectrafit.plugins.protocol import SpectraFitPlugin


class AnalysisPlugin:
    """Plugin for advanced statistical analysis."""

    name = "analysis"
    version = "1.0.0"
    description = "Advanced statistical analysis tools"

    def register_commands(self, parent_app: typer.Typer) -> None:
        # Create a subgroup for analysis commands
        analysis_app = typer.Typer(help="Statistical analysis commands")

        @analysis_app.command(name="correlation")
        def correlation_analysis() -> None:
            """Perform correlation analysis on fitting results."""
            typer.echo("Running correlation analysis...")

        @analysis_app.command(name="residuals")
        def residual_analysis() -> None:
            """Analyze fitting residuals."""
            typer.echo("Analyzing residuals...")

        # Register the subgroup
        parent_app.add_typer(analysis_app, name="analysis")

    def register_models(self) -> list[type]:
        return []
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
try:
    # Your plugin logic
    ...
except ImportError as e:
    typer.echo(f"❌ Missing dependencies: {e}", err=True)
    raise typer.Exit(1) from e
except ValueError as e:
    typer.echo(f"❌ Invalid input: {e}", err=True)
    raise typer.Exit(1) from e
```

### 2. Dependencies

Declare optional dependencies in `pyproject.toml`:

```toml
[project.optional-dependencies]
my-plugin = [
    "pandas>=2.0.0",
    "matplotlib>=3.5.0",
]
```

### 3. Type Hints

Use type hints for better IDE support and validation:

```python
from typing import Annotated
from pathlib import Path

def my_command(
    infile: Annotated[Path, typer.Argument(...)],
    verbose: Annotated[bool, typer.Option(...)] = False,
) -> None:
    ...
```

### 4. Help Text

Provide clear help text for all commands and options:

```python
@parent_app.command(name="my-command")
def my_command(
    infile: Annotated[
        Path,
        typer.Argument(
            help="Input file containing spectral data in CSV format",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
) -> None:
    """Process spectral data with custom algorithm.

    This command reads spectral data from a CSV file and applies
    a custom processing algorithm to extract features.
    """
    ...
```

### 5. Testing

Create tests for your plugin:

```python
from typer.testing import CliRunner
from spectrafit.cli.main import app

runner = CliRunner()

def test_my_plugin():
    result = runner.invoke(app, ["plugins", "my-command", "test.txt"])
    assert result.exit_code == 0
    assert "Processing" in result.output
```

## Plugin Distribution

### Publishing to PyPI

1. Create a proper package structure:

```
my-spectrafit-plugin/
├── pyproject.toml
├── README.md
├── LICENSE
└── my_plugin/
    ├── __init__.py
    └── plugin.py
```

2. Configure `pyproject.toml`:

```toml
[project]
name = "my-spectrafit-plugin"
version = "1.0.0"
description = "My custom SpectraFit plugin"
dependencies = [
    "spectrafit>=2.0.0",
]

[project.entry-points."spectrafit.plugins"]
my-plugin = "my_plugin.plugin:MyPlugin"
```

3. Publish:

```bash
python -m build
twine upload dist/*
```

## Troubleshooting

### Plugin Not Discovered

1. Check entry point configuration in `pyproject.toml`
2. Verify plugin class implements `SpectraFitPlugin` protocol
3. Reinstall package: `pip install -e .`
4. List plugins: `spectrafit plugins list -v`

### Import Errors

1. Check all dependencies are installed
2. Use try-except blocks for optional imports
3. Provide clear error messages

### Command Conflicts

1. Use unique command names
2. Check existing commands: `spectrafit plugins list`
3. Consider using subcommand groups

## Resources

- [SpectraFit Documentation](https://anselmoo.github.io/spectrafit/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Python Entry Points](https://packaging.python.org/specifications/entry-points/)

## Support

- GitHub Issues: [SpectraFit Issues](https://github.com/Anselmoo/spectrafit/issues)
- Discussions: [SpectraFit Discussions](https://github.com/Anselmoo/spectrafit/discussions)
