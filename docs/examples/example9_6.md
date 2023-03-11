---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.0
  kernelspec:
    display_name: .venv
    language: python
    name: python3
---

## Global Fitting of a series of spectra

```python
import pandas as pd
from spectrafit.plugins import notebook as nb
```

```python
df = pd.read_csv(
    "https://raw.githubusercontent.com/Anselmoo/spectrafit/1cda9e0d93f9d0536380075e75fac50459555b99/Examples/data_global.csv"
)
```

### This example shows how to fit a series of spectra with a common model

To activate the _global fitting_ routine, `y_column` has to be defined to
a list of column names and not a single column name. The list of column names
will be selected for the fitting.

```python
spn = nb.SpectraFitNotebook(
    df=df, x_column="energy", y_column=["y_1", "y_2", "y_3"], fname="example9_6"
)
```

### Defining the model as a function of the parameters

The `initial model` is defined as a function of the parameters as for 2D fitting.

```python
initial_model = [
    {
        "pseudovoigt": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
            "center": {"max": 2, "min": -2, "vary": True, "value": 0},
            "fwhmg": {"max": 0.3, "min": 0.02, "vary": True, "value": 0.1},
            "fwhml": {"max": 0.2, "min": 0.01, "vary": True, "value": 0.1},
        }
    },
    {
        "gaussian": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.3},
            "center": {"max": 2.0, "min": 0, "vary": True, "value": 2},
            "fwhmg": {"max": 0.3, "min": 0.02, "vary": True, "value": 0.1},
        }
    },
    {
        "gaussian": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.3},
            "center": {"max": 3.5, "min": 1.5, "vary": True, "value": 2.5},
            "fwhmg": {"max": 0.4, "min": 0.02, "vary": True, "value": 0.2},
        }
    },
    {
        "gaussian": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.3},
            "center": {"max": 3.5, "min": 2, "vary": True, "value": 2.5},
            "fwhmg": {"max": 0.4, "min": 0.02, "vary": True, "value": 0.3},
        }
    },
    {
        "gaussian": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.3},
            "center": {"max": 4.5, "min": 3, "vary": True, "value": 2.5},
            "fwhmg": {"max": 0.4, "min": 0.02, "vary": True, "value": 0.3},
        }
    },
    {
        "gaussian": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.3},
            "center": {"max": 4.7, "min": 3.7, "vary": True, "value": 3.8},
            "fwhmg": {"max": 0.4, "min": 0.02, "vary": True, "value": 0.3},
        }
    },
]
spn.solver_model(initial_model=initial_model, show_plot=True, show_metric=False)
```

#### Note:

Currently, the global fitting routine provides each spectrum as its own.
This also allows to use other color schemes.


![](https://github.com/Anselmoo/spectrafit/raw/main/docs/examples/images/Figure_9_6.png)
