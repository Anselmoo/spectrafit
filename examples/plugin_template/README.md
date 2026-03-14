## SpectraFit plugin template

This directory is a copyable template for third-party SpectraFit plugins.

SpectraFit v2 ships an **external plugin framework**:

- built-in top-level commands such as `spectrafit jupyter` are not plugins
- Mössbauer plugin entry points do not ship in the core package
- third-party packages can register commands through the
  `spectrafit.plugins` entry-point group

The template intentionally keeps packaging metadata minimal. A plugin package
only needs to:

- depend on `spectrafit` for the public plugin surface
- depend on `typer` if it imports Typer directly to register CLI commands
- expose a plugin class through the `spectrafit.plugins` entry-point group

### Template layout

```text
plugin_template/
├── pyproject.toml
└── src/
    └── spectrafit_example_plugin/
        ├── __init__.py
        ├── materializer.py
        └── plugin.py
```

### Included example command

The template now includes a real notebook-materializer command:

```bash
spectrafit plugins example-materialize-notebook path/to/input.toml \
  --output notebook.ipynb \
  --artifact-name demo-fit
```

What it does:

- loads an existing SpectraFit config file
- converts that config into typed notebook sections such as `FitParameter(...)`,
  `Component(...)`, `DataConfig(...)`, and `UnifiedFittingConfig(...)`
- keeps the notebook pointed at a local CSV such as `data.csv`
- rebuilds the validated config from those typed sections inside the notebook
- preserves the lower-level `SpectraFitNotebook.from_config(...)` execution flow used for advanced notebook integrations

Useful options:

- `--data-path local.csv` to override the CSV file loaded inside the notebook
- `--title "Custom notebook title"` to override the default heading
- `--description "..."` to inject your own intro text

### How to use it

1. Copy this directory to a new repository or package directory.
2. Rename `spectrafit_example_plugin` to your package name.
3. Update the project metadata in `pyproject.toml`.
   - keep only the metadata your standalone plugin package actually needs
   - keep `typer` as a direct dependency if your plugin imports it directly
   - point the `spectrafit.plugins` entry point at your plugin class
4. Replace the example command in `plugin.py` with your real functionality, or
   keep the notebook materializer as a starting point for config-to-notebook
   workflows.
5. Install the package and verify discovery with:

```bash
pip install -e .
spectrafit plugins list
```
