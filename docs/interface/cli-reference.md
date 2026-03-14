# CLI Reference

SpectraFit v2 uses a subcommand-based CLI.

For migration notes from the legacy single-command flow, see
[v2 migration guide](migration-v2.md).

## Command overview

| Command | Purpose | Example |
| --- | --- | --- |
| `spectrafit fit [CONFIG]` | Run a fit from a validated configuration file | `spectrafit fit fitting_input.toml --outfile run_01` |
| `spectrafit validate [CONFIG]` | Validate a configuration file without fitting | `spectrafit validate fitting_input.toml --verbose` |
| `spectrafit convert INPUT` | Convert config files between TOML / JSON / YAML or materialize an `.ipynb` notebook | `spectrafit convert input.json --format toml` |
| `spectrafit report RESULTS.json` | Render saved result files as text / markdown / json | `spectrafit report results.json --format markdown` |
| `spectrafit init` | Scaffold a starter CLI / Jupyter project | `spectrafit init` |
| `spectrafit new-config` | Print a starter v2 configuration file | `spectrafit new-config --format toml` |
| `spectrafit plugins list` | List external plugins discovered through entry points | `spectrafit plugins list` |
| `spectrafit jupyter` | Launch the first-class Jupyter interface | `spectrafit jupyter` |

## `fit`

`spectrafit fit [CONFIG]`

- accepts an optional config path
- when omitted, SpectraFit resolves the config from `SPECTRAFIT_CONFIG`
  or the default app-dir config
- fitting options exposed on the CLI control output behavior, not model structure

Common options:

- `--outfile`, `-o`: output prefix for exported result files
- `--noplot`, `-np`: disable plotting
- `--verbose`, `-vb`: output verbosity (`0`, `1`, `2`)

Examples:

```bash
spectrafit fit fitting_input.toml
spectrafit fit my_fit.json --outfile xps_run --verbose 2
spectrafit fit --noplot
```

## `validate`

`spectrafit validate [CONFIG]`

Examples:

```bash
spectrafit validate fitting_input.toml
spectrafit validate --verbose
```

## `convert`

`spectrafit convert INPUT --format {json|yaml|toml|ipynb}`

Examples:

```bash
spectrafit convert input.json --format yaml
spectrafit convert fitting_input.toml --format json --output converted.json
spectrafit convert fitting_input.toml --format ipynb --output analysis.ipynb
```

## `report`

`spectrafit report RESULTS.json`

Common options:

- `--format`, `-f`: `text`, `markdown`, or `json`
- `--output`, `-o`: write the rendered report to a file
- `--section`, `-s`: select `summary`, `variables`, `statistics`, `correlation`

Examples:

```bash
spectrafit report spectrafit_results_summary.json
spectrafit report results.json --format markdown --output report.md
```

## `init`

`spectrafit init` starts the interactive project scaffold wizard and can generate:

- a v2 configuration file
- a starter Jupyter notebook
- both assets together

The generated starter notebook uses the same one-import notebook workflow shown
throughout the docs: `import spectrafit.notebook as sf`, compact
`sf.peak(...)` / `sf.background(...)` builders, and bundled `result.save(...)`
exports.

## `new-config`

`spectrafit new-config` prints a starter v2 configuration document.

Examples:

```bash
spectrafit new-config --format toml
spectrafit new-config --format json --num-peaks 2
```

## `plugins`

The `plugins` command group is reserved for **external entry-point plugins**.

Core SpectraFit does not currently ship built-in `spectrafit.plugins` entry points.
In particular:

- Jupyter is a top-level command, not a plugin subcommand
- Mössbauer plugin entry points are not bundled with the core package

To build an external plugin, see
[Plugin Development Guide](../plugins/plugin-development-guide.md)
and the repository template under `examples/plugin_template/`.
