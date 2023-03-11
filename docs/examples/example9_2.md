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

## Using of themes for the plots

For working with different color themes, you can import `color_schemas` into the Notebook and overwrite the default theme.


```python
# Loading packages and default data
from spectrafit.plugins import notebook as nb
import pandas as pd

df = pd.read_csv(
    "https://raw.githubusercontent.com/Anselmoo/spectrafit/main/Examples/data.csv"
)
```


### Loading of the dark color theme

```python
from spectrafit.plugins import color_schemas as cs

spn = nb.SpectraFitNotebook(
    df=df,
    x_column="Energy",
    y_column="Noisy",
    color=cs.DraculaColor(),
    font=cs.DraculaFont(),
)
```

### Define the fitting model as usual

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

### Run fitting and plot the results in the dark theme

```python
spn.solver_model(initial_model=initial_model)
```


![example_9_2](https://github.com/Anselmoo/spectrafit/blob/e2f1616a2ca0eda15f2de1d1aa25281b3e05fc8c/docs/examples/images/Figure_9_2.png?raw=true)


![example_9_2_](https://github.com/Anselmoo/spectrafit/blob/617774defc5a42da302b7c594ccb10d3974ebe0c/docs/examples/images/Figure_9_2_m.png?raw=true)
