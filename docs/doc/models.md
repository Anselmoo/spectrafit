---
title: "Implemented Models in SpectraFit"
description: "Comprehensive documentation of all mathematical models available in SpectraFit, including peak shapes, background functions, and their parameters"
tags:
  - models
  - peak-shapes
  - distributions
  - background
  - fitting-functions
---

# Implemented Models in SpectraFit

**SpectraFit** provides a wide range of mathematical models for fitting spectroscopic data. This page documents all the available models, their parameters, and examples of their use.

!!! info "About implemented modxels"

    In principle, every model can bexx implemented in **SpectraFit** by extending the module `spectrafit.models` with new functions. It is important to extend the `raise` check in both `solver_model` and `calculated_model` for new function names.

    See the [lmfit custom model example](https://lmfit.github.io/lmfit-py/examples/documentation/model_two_components.html#sphx-glr-examples-documentation-model-two-components-py) for more details.

!!! tip "Section navigation"

    Use the navigation on the left to quickly jump between model types, constants, and visualization examples.

## Model Notation Reference

=== "Model Notation"

| Method              | Old Notation | New Notation |
| ------------------- | ------------ | ------------ |
| **Gaussian-FWHM**   | `fwhm`       | `fwhmg`      |
| **Lorentzian-FWHM** | `fwhm`       | `fwhml`      |
| **Pseudo-Voigt**    | `fwhm_g`     | `fwhmg`      |
| **Pseudo-Voigt**    | `fwhm_l`     | `fwhml`      |
| **Voigt**           | `fwhm`       | `fwhmv`      |

## List of Implemented Models

<div class="grid cards" markdown>

- :material-function-variant: **[Gaussian Distribution](#gaussian-distribution)**

  Bell-shaped curve widely used for modeling spectral peaks.

- :material-function-variant: **[Lorentzian Distribution](#lorentzian-distribution)**

  Distribution with wider tails than Gaussian, common in resonance phenomena.

- :material-function-variant: **[Pseudo-Voigt Distribution](#pseudo-voigt-distribution)**

  Linear combination of Gaussian and Lorentzian profiles.

- :material-function-variant: **[Voigt Distribution](#voigt-distribution)**

  Convolution of Gaussian and Lorentzian profiles.

- :material-chart-line: **[Exponential Function](#exponential-function)**

  Model for exponential decay or growth processes.

- :material-chart-line: **[Power Function](#power-function)**

  Function with a variable exponent.

- :material-chart-line-variant: **[Linear Function](#linear-function)**

  Basic linear background model.

- :material-division-box: **[Constant Function](#constant-function)**

  Flat background with a single amplitude parameter.

- :material-function: **[Error Function (Erf)](#error-function)**

  Sigmoid curve used for step-like transitions.

- :material-step-forward: **[Heaviside Function](#heaviside-function)**

  Step function for modeling abrupt changes.

- :material-chart-bell-curve: **[Arctangent Function](#arctangent-function)**

  Smooth transition function.

- :material-chart-line: **[Logarithmic Function](#logarithmic-function)**

  Natural logarithm function for transforming data.

- :material-chart-bell-curve: **[Complex Gaussian](#complex-gaussian)**

  Gaussian distribution with complex component.

- :material-chart-bell-curve: **[Complex Lorentzian](#complex-lorentzian)**

  Lorentzian distribution with complex component.

- :material-chart-bell-curve: **[Complex Voigt](#complex-voigt)**

  Voigt distribution with complex component.

- :material-chart-line-variant: **[Polynomial (2nd Order)](#polynomial-2nd-order)**

  Quadratic polynomial for curved backgrounds.

- :material-chart-line-variant: **[Polynomial (3rd Order)](#polynomial-3rd-order)**

  Cubic polynomial for more complex backgrounds.

- :material-chart-bell-curve: **[Pearson Type I](#pearson-type-i)**

  Beta distribution for asymmetric peaks.

- :material-chart-bell-curve: **[Pearson Type II](#pearson-type-ii)**

  Special case of Type I with symmetric shape.

- :material-chart-bell-curve: **[Pearson Type III](#pearson-type-iii)**

  Gamma distribution for asymmetric peaks.

- :material-chart-bell-curve: **[Pearson Type IV](#pearson-type-iv)**

  Flexible distribution with four parameters.

</div>

## Peak Distribution Models

### Gaussian Distribution

The Gaussian distribution is a symmetric bell-shaped curve defined by its amplitude, center, and width:

$$f(x) = \frac{A}{\sigma\sqrt{2\pi}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$$

Where:

- $A$ is the amplitude
- $\mu$ is the center (mean)
- $\sigma$ is related to the full width at half maximum (FWHM) by $\text{FWHM} = 2\sigma\sqrt{2\ln{2}}$

!!! example "Gaussian Model Parameters"

    ```json
         {
        "peaks": {
          "1": {
            "gaussian": {
              "amplitude": {"max": 2, "min": 0, "vary": true, "value": 1},
              "center": {"max": 2, "min": -2, "vary": true, "value": 0},
              "fwhmg": {"max": 0.5, "min": 0.02, "vary": true, "value": 0.1}
            }
          }
        }
      }
    ```

### Lorentzian Distribution

The Lorentzian distribution, also known as the Cauchy distribution, is characterized by wider tails compared to the Gaussian distribution:

$$f(x) = \frac{A}{\pi} \frac{\gamma}{(x-x_0)^2 + \gamma^2}$$

Where:

- $A$ is the amplitude
- $x_0$ is the center
- $\gamma$ is the half-width at half-maximum (HWHM)

!!! example "Lorentzian Model Parameters"

    ```json
        {
          "peaks": {
            "1": {
              "lorentzian": {
                "amplitude": {"max": 2, "min": 0, "vary": true, "value": 1},
                "center": {"max": 2, "min": -2, "vary": true, "value": 0},
                "fwhml": {"max": 0.5, "min": 0.02, "vary": true, "value": 0.1}
              }
            }
          }
        }
    ```

### Pseudo-Voigt Distribution

The Pseudo-Voigt distribution is a linear combination of Gaussian and Lorentzian distributions:

$$f(x) = \eta \cdot L(x) + (1-\eta) \cdot G(x)$$

Where:

- $\eta$ is the mixing parameter (calculated from fwhmg and fwhml)
- $L(x)$ is the Lorentzian component
- $G(x)$ is the Gaussian component

!!! example "Pseudo-Voigt Model Parameters"

    ```json
      {
        "peaks": {
          "1": {
            "pseudovoigt": {
              "amplitude": {"max": 2, "min": 0, "vary": true, "value": 1},
              "center": {"max": 2, "min": -2, "vary": true, "value": 0},
              "fwhmg": {"max": 0.5, "min": 0.02, "vary": true, "value": 0.1},
              "fwhml": {"max": 0.5, "min": 0.01, "vary": true, "value": 0.1}
            }
          }
        }
      }
    ```

### Voigt Distribution

The Voigt distribution is the convolution of a Gaussian and a Lorentzian distribution:

$$f(x) = \int_{-\infty}^{\infty} G(x') \cdot L(x-x') dx'$$

This distribution is implemented using the Faddeeva function.

!!! example "Voigt Model Parameters"

    ```json
      {
        "peaks": {
          "1": {
            "voigt": {
              "amplitude": {"max": 2, "min": 0, "vary": true, "value": 1},
              "center": {"max": 2, "min": -2, "vary": true, "value": 0},
              "fwhmv": {"max": 0.5, "min": 0.02, "vary": true, "value": 0.1},
              "gamma": {"max": 0.5, "min": 0.01, "vary": true, "value": 0.1}
            }
          }
        }
      }
    ```

## Background Models

### Exponential Function

$$f(x) = A \cdot \exp(b \cdot x + c)$$

### Power Function

$$f(x) = A \cdot x^b + c$$

### Linear Function

$$f(x) = A \cdot x + b$$

### Constant Function

$$f(x) = A$$

## Step Functions

### Error Function

$$f(x) = A \cdot \text{erf}\left(\frac{x-\mu}{\sigma\sqrt{2}}\right) + b$$

### Heaviside Function

$$f(x) = A \cdot H(x-x_0) + b$$

Where $H$ is the Heaviside step function.

### Arctangent Function

$$f(x) = A \cdot \tan^{-1}\left(\frac{x-x_0}{w}\right) + b$$

## Other Functions

### Logarithmic Function

$$f(x) = A \cdot \ln(b \cdot x + c) + d$$

### Complex Gaussian

Gaussian distribution with a complex component.

### Complex Lorentzian

Lorentzian distribution with a complex component.

### Complex Voigt

Voigt distribution with a complex component.

### Polynomial (2nd Order)

$$f(x) = a_0 + a_1 \cdot x + a_2 \cdot x^2$$

### Polynomial (3rd Order)

$$f(x) = a_0 + a_1 \cdot x + a_2 \cdot x^2 + a_3 \cdot x^3$$

## Pearson Distributions

### Pearson Type I

Beta distribution with flexible shape parameters.

### Pearson Type II

Special case of Type I with symmetric shape.

### Pearson Type III

Gamma distribution for asymmetric peaks.

### Pearson Type IV

Flexible distribution with four parameters.

## Important Constants for the Models

For calculating the models, a few math constants are needed, which are implemented in the `constants` module.

::: spectrafit.models.Constants

## Visualization of the Models

!!! info "About Peaks' Components"

    Comparing components of the peaks in a table is important for identifying trends, patterns, and outliers in your data.
    Having this information in a table format makes it easier to visualize, interpret, and communicate results.

    This can be seen in [example9_3.ipynb](https://github.com/Anselmoo/spectrafit/blob/main/docs/examples/example9_3.ipynb).

    ```python
    from spectrafit.plugins import notebook as nb
    ...
    spn.solver_model(initial_model=initial_model, show_peaks=True)
    ```
    This provides an interactive table and allows exporting the iterative results as a CSV file.

??? example "Download Peak Components Example CSV"

    The following dataset demonstrates the structure of exported peak components. You can download and explore it:

    [Download dataset](../assets/data/peaks_components_example.csv)

    _This CSV contains columns for each parameter and rows for initial, model, and best values._

## Related Content

- [Expression Syntax](expression.md)
- [Fitting Documentation](fitting.md)
- [API Reference](../api/modelling_api.md)
- [Changelog](../changelog.md)
