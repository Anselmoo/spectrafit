[![CI - Python Package](https://github.com/Anselmoo/spectrafit/actions/workflows/python-ci.yml/badge.svg?branch=main)](https://github.com/Anselmoo/spectrafit/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/Anselmoo/spectrafit/branch/main/graph/badge.svg?token=pNIMKwWsO2)](https://codecov.io/gh/Anselmoo/spectrafit)
[![PyPI](https://img.shields.io/pypi/v/spectrafit?logo=PyPi&logoColor=yellow)](https://pypi.org/project/spectrafit/)
[![Conda](https://img.shields.io/conda/v/conda-forge/spectrafit?label=Anaconda.org&logo=anaconda)](https://github.com/conda-forge/spectrafit-feedstock)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/spectrafit?color=gree&logo=Python&logoColor=yellow)](https://pypi.org/project/spectrafit/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Anselmoo/spectrafit/main.svg)](https://results.pre-commit.ci/latest/github/Anselmoo/spectrafit/main)

<p align="center">
<img src="https://github.com/Anselmoo/spectrafit/blob/c5f7ee05e5610fb8ef4e237a88f62977b6f832e5/docs/images/spectrafit_synopsis.png?raw=true">
</p>

# SpectraFit

`SpectraFit` is a tool for quick data fitting based on the regular
expression of distribution and linear functions via command line or
[Jupyter Notebook](https://jupyter.org). Furthermore, it can be also used as
a module in existing python code. A previous version of `SpectraFit` was used
for the following publication:

- [Measurement of the Ligand Field Spectra of Ferrous and Ferric Iron Chlorides Using 2p3d RIXS](https://pubs.acs.org/doi/abs/10.1021/acs.inorgchem.7b00940)

Now, it is completely rewritten and is more flexible. It is supporting all
common ASCII-data formats and it runs on `Linux`, `Windows`, and `MacOS`.

## Scope

- Fitting of 2D data, also with multiple columns as _global fitting_
- Using established and advanced solver methods
- Extensibility of the fitting function
- Guarantee traceability of the fitting results
- Saving all results in a _SQL-like-format_ (`CSV`) for publications
- Saving all results in a _NoSQL-like-format_ (`JSON`) for project management
- Having an API interface for Graph-databases

## Installation

via pip:

```terminal
pip install spectrafit

# with support for Jupyter Notebook

pip install spectrafit[jupyter]

# with all upcomming features

pip install spectrafit[all]

# Upgrade

pip install spectrafit --upgrade
```

via conda, see also [conda-forge](https://github.com/conda-forge/spectrafit-feedstock):

```terminal
conda install -c conda-forge spectrafit

# with support for Jupyter Notebook

conda install -c conda-forge spectrafit-jupyter

# with all upcomming features

conda install -c conda-forge spectrafit-all
```

## Usage

`SpectraFit` needs as command line tool only two things:

1. The reference data, which should be fitted.
2. The input file, which contains the initial model.

As model files [json](https://en.wikipedia.org/wiki/JSON),
[toml](https://en.wikipedia.org/wiki/TOML), and
[yaml](https://en.wikipedia.org/wiki/YAML) are supported. By making use of the
python `**kwargs` feature, the input file can call most of the following
functions of [LMFIT](https://lmfit.github.io/lmfit-py/index.html). LMFIT is the
workhorse for the fit optimization, which is macro wrapper based on:

1. [NumPy](https://www.numpy.org/)
2. [SciPy](https://www.scipy.org/)
3. [uncertainties](https://pythonhosted.org/uncertainties/)

In case of `SpectraFit`, we have further extend the package by:

1. [Pandas](https://pandas.pydata.org/)
2. [statsmodels](https://www.statsmodels.org/stable/index.html)
3. [numdifftools](https://github.com/pbrod/numdifftools)
4. [Matplotlib](https://matplotlib.org/) in combination with
   [Seaborn](https://seaborn.pydata.org/)

```terminal
spectrafit data_file.txt -i input_file.json
```

```terminal
usage: spectrafit [-h] [-o OUTFILE] [-i INPUT] [-ov] [-e0 ENERGY_START]
                  [-e1 ENERGY_STOP] [-s SMOOTH] [-sh SHIFT] [-c COLUMN COLUMN]
                  [-sep {       ,,,;,:,|, ,s+}] [-dec {.,,}] [-hd HEADER]
                  [-g {0,1,2}] [-auto] [-np] [-v] [-vb {0,1,2}]
                  infile

Fast Fitting Program for ascii txt files.

positional arguments:
  infile                Filename of the spectra data

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Filename for the export, default to set to
                        'spectrafit_results'.
  -i INPUT, --input INPUT
                        Filename for the input parameter, default to set to
                        'fitting_input.toml'.Supported fileformats are:
                        '*.json', '*.yml', '*.yaml', and '*.toml'
  -ov, --oversampling   Oversampling the spectra by using factor of 5;
                        default to False.
  -e0 ENERGY_START, --energy_start ENERGY_START
                        Starting energy in eV; default to start of energy.
  -e1 ENERGY_STOP, --energy_stop ENERGY_STOP
                        Ending energy in eV; default to end of energy.
  -s SMOOTH, --smooth SMOOTH
                        Number of smooth points for lmfit; default to 0.
  -sh SHIFT, --shift SHIFT
                        Constant applied energy shift; default to 0.0.
  -c COLUMN COLUMN, --column COLUMN COLUMN
                        Selected columns for the energy- and intensity-values;
                        default to '0' for energy (x-axis) and '1' for intensity
                        (y-axis). In case of working with header, the column
                        should be set to the column names as 'str'; default
                        to 0 and 1.
  -sep { ,,,;,:,|, ,s+}, --separator { ,,,;,:,|, ,s+}
                        Redefine the type of separator; default to ' '.
  -dec {.,,}, --decimal {.,,}
                        Type of decimal separator; default to '.'.
  -hd HEADER, --header HEADER
                        Selected the header for the dataframe; default to None.
  -cm COMMENT, --comment COMMENT
                        Lines with comment characters like '#' should not be
                        parsed; default to None.
  -g {0,1,2}, --global_ {0,1,2}
                        Perform a global fit over the complete dataframe. The
                        options are '0' for classic fit (default). The
                        option '1' for global fitting with auto-definition
                        of the peaks depending on the column size and '2'
                        for self-defined global fitting routines.
  -auto, --autopeak     Auto detection of peaks in the spectra based on `SciPy`.
                        The position, height, and width are used as estimation
                        for the `Gaussian` models.The default option is 'False'
                        for  manual peak definition.
  -np, --noplot         No plotting the spectra and the fit of `SpectraFit`.
  -v, --version         Display the current version of `SpectraFit`.
  -vb {0,1,2}, --verbose {0,1,2}
                        Display the initial configuration parameters and fit
                        results, as a table '1', as a dictionary '2', or not in
                        the terminal '0'. The default option is set to 1 for
                        table `printout`.
```

### Jupyter Notebook

Open the `Jupyter Notebook` and run the following code:

```terminal
spectrafit-jupyter
```

or via Docker Image:

```terminal
docker pull ghcr.io/anselmoo/spectrafit:latest
docker run -it -p 8888:8888 spectrafit:latest
```

or just:

```terminal
docker run -p 8888:8888 ghcr.io/anselmoo/spectrafit:latest
```

Next define your initial model and the reference data:

```python
from spectrafit.plugins.notebook import SpectraFitNotebook
import pandas as pd

df = pd.read_csv(
    "https://raw.githubusercontent.com/Anselmoo/spectrafit/main/Examples/data.csv"
)

initial_model = [
    {
        "pseudovoigt": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
            "center": {"max": 2, "min": -2, "vary": True, "value": 0},
            "fwhmg": {"max": 0.4, "min": 0.1, "vary": True, "value": 0.21},
            "fwhml": {"max": 0.4, "min": 0.1, "vary": True, "value": 0.21},
        }
    },
    {
        "pseudovoigt": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
            "center": {"max": 2, "min": -2, "vary": True, "value": 1},
            "fwhmg": {"max": 0.4, "min": 0.1, "vary": True, "value": 0.21},
            "fwhml": {"max": 0.4, "min": 0.1, "vary": True, "value": 0.21},
        }
    },
    {
        "pseudovoigt": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
            "center": {"max": 2, "min": -2, "vary": True, "value": 1},
            "fwhmg": {"max": 0.4, "min": 0.1, "vary": True, "value": 0.21},
            "fwhml": {"max": 0.4, "min": 0.1, "vary": True, "value": 0.21},
        }
    },
]
spf = SpectraFitNotebook(df=df, x_column="Energy", y_column="Noisy")
spf.solver_model(initial_model)
```

Which results in the following output:

![img_jupyter](https://github.com/Anselmoo/spectrafit/blob/8962a277b0c3d2aa05970617f0ac323a07de2fec/docs/images/jupyter_plot.png?raw=true)

## Documentation

Please see the [extended documentation](https://anselmoo.github.io/spectrafit/)
for the full usage of `SpectraFit`.
