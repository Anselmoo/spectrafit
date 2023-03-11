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

<!-- #region -->
## Regular Usage of the Jupyter-Notebook extension for `SpectraFit`

This notebook shows how to use the Jupyter-Notebook extension for `SpectraFit` to fit a spectrum. In order to use the extension, you need to install the `SpectraFit` like the following:

```bash
pip install spectrafit[jupyter]
```

or straight in the notebook:

```bash
! pip install spectrafit[jupyter]
```
Then, you need to enable the extension by running the following command in the terminal:
<!-- #endregion -->

```python
from spectrafit.plugins import notebook as nb
```

Other regular packages are already installed:

1. `numpy`
2. `matplotlib`
3. `scipy`
4. `pandas`

So that the data / spectra can be loaded and plotted.


```python
import pandas as pd
import matplotlib

# %matplotlib inline
```

```python
df = pd.read_csv(
    "https://raw.githubusercontent.com/Anselmoo/spectrafit/main/Examples/data.csv"
)
df.plot(x="Energy", y="Noisy", kind="line", label="Spectra")
```

The `spectra` aboive shows a _pseudo_ 2p3d spectrum, see also: https://doi.org/10.1021/acs.inorgchem.8b01550


### Load the data into the notebook-plugin of `SpectraFit`

```python
spn = nb.SpectraFitNotebook(df=df, x_column="Energy", y_column="Noisy")
```

### Define the fitting model

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
```

### Run the fitting with the proposed `initial_model`

```python
spn.solver_model(initial_model=initial_model)
```

![example_9_1](https://github.com/Anselmoo/spectrafit/blob/e2f1616a2ca0eda15f2de1d1aa25281b3e05fc8c/docs/examples/images/Figure_9_1.png?raw=true)
![example_9_1_m](https://github.com/Anselmoo/spectrafit/blob/617774defc5a42da302b7c594ccb10d3974ebe0c/docs/examples/images/Figure_9_1_m.png?raw=true)


### Show the dataframe with the fitted parameters

```python
spn.display_fit_df(mode="interactive")
```

### Metric Plot of the fitted model

`SpectraFit` also shows the metric of the fitted model.
The plot shows the metric of the fitted model for each run. The metric consits of
the `goodness of fit` and the `regression metric` of the model. By default, the
`Akaike Information Criterion` and `Bayesian Information Criteria` are used
for the bar plot and the `Mean Squared Error` for the line plot.

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
            "center": {"max": 3.5, "min": 1.5, "vary": True, "value": 2.5},
            "fwhmg": {"max": 0.4, "min": 0.02, "vary": True, "value": 0.2},
        }
    },
    {
        "gaussian": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.3},
            "center": {"max": 3.25, "min": 1.8, "vary": True, "value": 2.5},
            "fwhmg": {"max": 0.4, "min": 0.02, "vary": True, "value": 0.3},
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
spn.solver_model(initial_model=initial_model, conf_interval=False)
```

### Fit Plot

![Figure_9_1_a1](https://github.com/Anselmoo/spectrafit/blob/617774defc5a42da302b7c594ccb10d3974ebe0c/docs/examples/images/Figure_9_1_a1.png?raw=true)


### Metric Blogs

![Figure_9_1_a2](https://github.com/Anselmoo/spectrafit/blob/617774defc5a42da302b7c594ccb10d3974ebe0c/docs/examples/images/Figure_9_1_a2.png?raw=true)
