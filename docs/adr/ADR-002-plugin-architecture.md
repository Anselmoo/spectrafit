# ADR-002: Plugin Architecture

## Status

**Accepted** - Implemented in v2.0.0

## Context

SpectraFit has several specialized features (RIXS visualization, Jupyter integration, Mössbauer models) that:

1. Have optional dependencies
2. May not be needed by all users
3. Could benefit from third-party extensions
4. Need clear extension points

The original implementation had:
- Standalone CLI apps (e.g., `spectrafit-rixs-visualizer`)
- Tightly coupled code in main application
- No clear plugin interface
- No discovery mechanism

## Decision

We implemented a **formal plugin architecture** with:

1. **Plugin Protocol**: `SpectraFitPlugin` defining the plugin interface
2. **Discovery System**: Using Python entry points and `importlib.metadata`
3. **Registry**: Centralized plugin management via `PluginRegistry`
4. **Built-in Plugins**: Convert existing features to plugins

### Plugin Protocol

```python
from typing import Protocol
import typer

class SpectraFitPlugin(Protocol):
    """Protocol for SpectraFit plugins."""
    
    name: str
    version: str
    description: str
    
    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register CLI commands with the parent Typer app."""
        ...
    
    def register_models(self) -> list[type]:
        """Return list of Pydantic models this plugin provides."""
        ...
```

### Entry Points

Plugins are discovered via entry points in `pyproject.toml`:

```toml
[project.entry-points."spectrafit.plugins"]
rixs = "spectrafit.plugins.rixs_plugin:RIXSPlugin"
jupyter = "spectrafit.plugins.jupyter_plugin:JupyterPlugin"
moessbauer = "spectrafit.plugins.moessbauer_plugin:MoessbauerPlugin"
```

### Plugin Discovery

```python
from spectrafit.plugins import get_plugin_registry

registry = get_plugin_registry()

# Discover all plugins
for plugin in registry.discover_plugins():
    plugin.register_commands(app)
```

## Consequences

### Positive

- ✅ **Extensibility**: Third parties can create plugins
- ✅ **Modularity**: Clean separation of concerns
- ✅ **Optional Features**: Users install only what they need
- ✅ **Clear Interface**: Well-defined plugin contract
- ✅ **Discovery**: Automatic plugin discovery via entry points
- ✅ **Testing**: Each plugin can be tested independently

### Negative

- ⚠️ **Complexity**: Added abstraction layer
- ⚠️ **Migration**: Existing features needed refactoring

### Neutral

- 📝 **Documentation**: New plugin development guide needed
- 📝 **Ecosystem**: Opens possibility for external plugins

## Built-in Plugins

### 1. RIXS Plugin

**Purpose**: Interactive RIXS plane visualization
**Dependencies**: `dash`, `dash-bootstrap-components`, `jupyter-dash`
**Commands**: `spectrafit plugins rixs <infile>`

### 2. Jupyter Plugin

**Purpose**: Jupyter Lab integration
**Dependencies**: `jupyterlab`, `plotly`, `dtale`
**Commands**: `spectrafit plugins jupyter`

### 3. Mössbauer Plugin

**Purpose**: Mössbauer spectroscopy models
**Dependencies**: None (uses core models)
**Commands**: `spectrafit plugins moessbauer-info`

## Plugin Development

### Creating a Plugin

```python
# my_plugin.py
import typer
from spectrafit.plugins import SpectraFitPlugin

class MyPlugin:
    name = "my-plugin"
    version = "1.0.0"
    description = "My custom plugin"
    
    def register_commands(self, parent_app: typer.Typer) -> None:
        @parent_app.command(name="mycommand")
        def my_command() -> None:
            print("Hello from my plugin!")
    
    def register_models(self) -> list[type]:
        return [MyModel1, MyModel2]
```

### Registering a Plugin

In `pyproject.toml`:

```toml
[project.entry-points."spectrafit.plugins"]
my-plugin = "my_package.my_plugin:MyPlugin"
```

## Alternatives Considered

### 1. No Plugin System

**Pros**: Simpler, no abstractions
**Cons**: Monolithic, hard to extend, optional deps always loaded

### 2. Namespace Packages

**Pros**: Python-native pattern
**Cons**: More complex, discovery issues, maintenance burden

### 3. Hooks/Callbacks

**Pros**: Lightweight
**Cons**: Less structured, no clear interface, harder to validate

## Migration Strategy

1. ✅ Create plugin protocol and discovery system
2. ✅ Convert RIXS visualizer to plugin
3. ✅ Convert Jupyter integration to plugin
4. ✅ Convert Mössbauer models to plugin
5. ⏳ Maintain backward compatibility with old CLI commands
6. ⏳ Document plugin development process
7. ⏳ Create plugin template/cookiecutter

## Related Decisions

- ADR-001: Typer CLI Migration (enables plugin commands)
- ADR-003: Subcommand Structure (plugins as subcommands)

## References

- [Python Entry Points](https://packaging.python.org/specifications/entry-points/)
- [PEP 544 - Protocols](https://www.python.org/dev/peps/pep-0544/)
- [importlib.metadata](https://docs.python.org/3/library/importlib.metadata.html)

## Revision History

| Date       | Version | Author       | Description          |
| ---------- | ------- | ------------ | -------------------- |
| 2025-01-15 | 1.0     | Copilot Team | Initial ADR creation |
