---
title: SpectraFit API Reference
description: Comprehensive API documentation for the SpectraFit package, covering all modules and functions
tags:
  - api
  - reference
  - functions
  - classes
  - modules
---

# SpectraFit API Reference

This section provides comprehensive documentation of the **SpectraFit** API,
allowing you to use the package programmatically in your own applications.

## Overview

The **SpectraFit** API is organized around canonical v2 surfaces for validated
configuration, fitting orchestration, notebook integration, reporting, and
typed model contracts.

!!! info "API Usage"

    The API documentation is intended for users who want to integrate **SpectraFit** into their own Python code or develop extensions to the package.

## Core API Modules

<div class="grid cards" markdown>

- :material-application: **[SpectraFit Command Surface](spectrafit_api.md)**

  CLI/runtime-facing entry surfaces and command orchestration helpers.

- :material-chart-scatter-plot: **[Plotting](plotting_api.md)**

  Functions for visualizing spectra and fitting results.

- :material-notebook: **[Jupyter Notebook](notebook_api.md)**

  APIs for interactive use in Jupyter notebooks.

- :material-function-variant: **[Modelling](modelling_api.md)**

  Typed components, registry-backed models, bundle composition, and naming.

- :material-file-document: **[Reporting](reporting_api.md)**

  Tools for generating reports and exporting results.

- :material-cog: **[Core](core_api.md)**

  Core utilities for data loading, preprocessing, postprocessing, and export.

- :material-database: **[Data Model](data_model_api.md)**

  Pydantic-owned data structures and API-facing schemas.

</div>

## API Usage Examples

Here's a simple example of using the **SpectraFit** API programmatically:

```python
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.output_config import OutputConfig

config = UnifiedFittingConfig.model_validate(
    {
        "data": {"infile": "sample.csv", "x_col": "energy", "y_col": "intensity"},
        "components": [
            {
                "id": "p1",
                "model": "gaussian",
                "parameters": {
                    "amplitude": {"value": 1.0, "min": 0.0, "max": 2.0, "vary": True},
                    "center": {"value": 0.0, "min": -2.0, "max": 2.0, "vary": True},
                    "fwhmg": {"value": 0.5, "min": 0.01, "max": 2.0, "vary": True},
                },
            }
        ],
    }
)
output = OutputConfig(outfile="spectrafit_results", noplot=True, verbose=1)

# Pass canonical models into the runtime pipeline or notebook surface.
```

## Integration with Other Packages

**SpectraFit** integrates with several other Python packages:

- **NumPy** and **Pandas** for data handling
- **Matplotlib** and **Plotly** for visualization
- **lmfit** for the underlying fitting engine
- **Jupyter** for interactive analysis

## Next Steps

After exploring the API, you may want to:

- Check the [Examples](../examples/index.md) for practical applications
- Learn about [Plugins](../plugins/index.md) to extend functionality
- Understand the [implementation details](../doc/index.md) of the algorithms
