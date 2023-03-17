!!! note "About the Notebook API"

    The **Notebook API** is a new feature in the v0.12.0 release of
    `SpectraFit` with major focus on working with Jupyter Notebooks.

    > The Notebook API is a work in progress and is subject to change.

::: spectrafit.plugins.notebook

## Color Scheme

For changing the _color scheme_ of the plots, additional color schemes can be
added to the `spectrafit.plugins.notebook` module. The color schemes are defined
as a pydantic `BaseSettings` class with the following attributes:

::: spectrafit.plugins.color_schemas

## Running SpectraFit in the _builtin_ Jupyter-Notebook

For running `SpectraFit` in the _builtin_ Jupyter-Notebook, the following
command can be used:

```bash
spectrafit-jupyter
```

And next, the `SpectraFitNotebook` class can be used for fitting the data:

```python
from spectrafit.plugins.notebook import SpectraFitNotebook
```
