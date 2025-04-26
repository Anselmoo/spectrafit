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

This section provides comprehensive documentation of the **SpectraFit** API, allowing you to use the package programmatically in your own applications.

## Overview

The **SpectraFit** API is organized into several modules, each providing specific functionality for spectral analysis. This reference documents all public classes, functions, and their parameters.

!!! info "API Usage"
The API documentation is intended for users who want to integrate **SpectraFit** into their own Python code or develop extensions to the package.

## Core API Modules

<div class="grid cards" markdown>

- :material-application: **[SpectraFit Core](spectrafit_api.md)**

  Main module providing the core functionality for spectral fitting.

- :material-chart-scatter-plot: **[Plotting](plotting_api.md)**

  Functions for visualizing spectra and fitting results.

- :material-notebook: **[Jupyter Notebook](notebook_api.md)**

  APIs for interactive use in Jupyter notebooks.

- :material-function-variant: **[Modelling](modelling_api.md)**

  Models and functions for peak fitting and background subtraction.

- :material-file-document: **[Reporting](reporting_api.md)**

  Tools for generating reports and exporting results.

- :material-tools: **[Tools](tools_api.md)**

  Utility functions for data preprocessing and manipulation.

- :material-database: **[Data Model](data_model_api.md)**

  Data structures and schemas used throughout the package.

- :material-file-swap: **[Converters & Visualizer](converter_api.md)**

  File format conversion and specialized visualization tools.

</div>

## API Usage Examples

Here's a simple example of using the **SpectraFit** API programmatically:

```python
import numpy as np
from spectrafit import spectrafit, models

# Generate sample data
x = np.linspace(-10, 10, 1000)
y = models.gaussian(x, amplitude=5, center=0, sigma=1) + np.random.normal(0, 0.1, size=len(x))

# Configure fitting parameters
parameters = {
    "peaks": {
        "1": {
            "gaussian": {
                "amplitude": {"value": 4, "min": 0, "max": 10, "vary": True},
                "center": {"value": 0.5, "min": -5, "max": 5, "vary": True},
                "sigma": {"value": 1.2, "min": 0.1, "max": 3, "vary": True}
            }
        }
    }
}

# Perform the fit
result = spectrafit.fit_spectrum(x, y, parameters)

# Access the results
fitted_params = result.best_values
fitted_curve = result.best_fit
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
- Learn about [Plugins](../plugins/file_converter.md) to extend functionality
- Understand the [implementation details](../doc/index.md) of the algorithms
