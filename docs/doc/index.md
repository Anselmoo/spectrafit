---
title: SpectraFit Documentation
description: Technical documentation covering the models, expressions, solvers, fitting methods, and statistics in SpectraFit
tags:
  - documentation
  - models
  - expressions
  - solvers
  - fitting
  - statistics
---

# SpectraFit Documentation

This section provides comprehensive technical documentation on the mathematical and computational foundations of **SpectraFit**.

## Overview

**SpectraFit** implements various mathematical models, fitting algorithms, and statistical methods to analyze spectral data with precision and flexibility. This documentation explains the theoretical background and implementation details.

!!! info "Documentation Scope"
    This section focuses on the technical aspects of **SpectraFit**. For usage instructions, see the [Interface](../interface/index.md) section.

## Core Components

<div class="grid cards" markdown>

- :material-function-variant: **[Models](models.md)**

  Detailed information about the mathematical models available for peak fitting.

- :material-code-braces: **[Expression](expression.md)**

  Guide to creating custom expressions for complex fitting scenarios.

- :material-calculator: **[Solvers](solver.md)**

  Technical details on the optimization algorithms used for fitting.

- :material-chart-line: **[Fitting](fitting.md)**

  Explanation of the fitting process and parameter optimization.

- :material-chart-bell-curve-cumulative: **[Statistics](statistics.md)**

  Overview of statistical analysis methods for evaluating fit quality.

</div>

## Mathematical Foundation

**SpectraFit** is built on rigorous mathematical principles for spectral analysis. The package includes:

- Peak shape functions (Gaussian, Lorentzian, Voigt, etc.)
- Background models (constant, linear, polynomial)
- Optimization algorithms for parameter fitting
- Statistical methods for fit quality assessment
- Error analysis and confidence intervals

## Scientific Applications

The models and methods implemented in **SpectraFit** are applicable to a wide range of scientific fields:

- X-ray Absorption Spectroscopy (XAS)
- X-ray Emission Spectroscopy (XES)
- Resonant Inelastic X-ray Scattering (RIXS)
- Raman Spectroscopy
- Infrared Spectroscopy
- Photoluminescence Spectroscopy
- Nuclear Magnetic Resonance (NMR)

## Next Steps

After understanding the technical foundations, you may want to explore:

- [Examples](../examples/example1.md) of applying these methods
- [API Reference](../api/modelling_api.md) for programmatic access to models
- [Plugins](../plugins/file_converter.md) for extending functionality
