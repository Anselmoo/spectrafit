[![CI - Python Package](https://github.com/Anselmoo/spectrafit/actions/workflows/python-ci.yml/badge.svg?branch=main)](https://github.com/Anselmoo/spectrafit/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/Anselmoo/spectrafit/branch/main/graph/badge.svg?token=pNIMKwWsO2)](https://codecov.io/gh/Anselmoo/spectrafit)
[![PyPI](https://img.shields.io/pypi/v/spectrafit?logo=PyPi&logoColor=yellow)](https://pypi.org/project/spectrafit/)
[![Conda](https://img.shields.io/conda/v/conda-forge/spectrafit?label=Anaconda.org&logo=anaconda)](https://github.com/conda-forge/spectrafit-feedstock)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/spectrafit?color=gree&logo=Python&logoColor=yellow)](https://pypi.org/project/spectrafit/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Anselmoo/spectrafit/main.svg)](https://results.pre-commit.ci/latest/github/Anselmoo/spectrafit/main)
[![doi](https://img.shields.io/badge/10.1021/acsomega.3c09262-blue?logo=DOI&logoColor=white)](https://pubs.acs.org/doi/full/10.1021/acsomega.3c09262)

<p align="center">
<img src="https://github.com/Anselmoo/spectrafit/blob/c5f7ee05e5610fb8ef4e237a88f62977b6f832e5/docs/images/spectrafit_synopsis.png?raw=true">
</p>

# SpectraFit

---

> Data Analysis Tool for All Kinds of Spectra

`SpectraFit` is a Python tool for quick data fitting based on the regular
expression of distribution and linear functions via the command line (CMD) or
[Jupyter Notebook](https://jupyter.org) It is designed to be easy to use and
supports all common ASCII data formats. SpectraFit runs on **Linux**,
**Windows**, and **MacOS**.

## Scope

- Fitting of 2D data, also with multiple columns as _global fitting_
- Using established and advanced solver methods
- Extensibility of the fitting function
- Guarantee traceability of the fitting results
- Saving all results in a _SQL-like-format_ (`CSV`) for publications
- Saving all results in a _NoSQL-like-format_ (`JSON`) for project management
- Having an API interface for Graph-databases

`SpectraFit` is a tool designed for researchers and scientists who require
immediate data fitting to a model. It proves to be especially beneficial for
individuals working with vast datasets or who need to conduct numerous fits
within a limited time frame. `SpectraFit's` adaptability to various platforms
and data formats makes it a versatile tool that caters to a broad spectrum of
scientific applications.

## Installation

Install the command-line tool:

```bash
pip install spectrafit
```

Install notebook support when you want to run the committed example notebooks:

```bash
pip install "spectrafit[jupyter]"
```

Optional extras:

```bash
pip install "spectrafit[graph]"   # graph-oriented extras
pip install "spectrafit[all]"     # all optional runtime extras
pip install --upgrade spectrafit
```

If you are working from this repository, the easiest scientist-friendly setup is:

```bash
git clone https://github.com/Anselmoo/spectrafit.git
cd spectrafit
uv sync --extra jupyter
```

via conda, see also
[conda-forge](https://github.com/conda-forge/spectrafit-feedstock):

```bash
conda install -c conda-forge spectrafit
```

## Quickstart with the shipped examples

The fastest way to learn SpectraFit v2 is to start from the committed examples
under [`examples/`](examples/README.md). Each example ships with:

- `data.csv` — synthetic input data you can inspect locally
- `input.toml` — readable v2 config used by both CLI and notebook flows
- `notebook.ipynb` — local Jupyter notebook rooted in the example directory
- `fit_validation.html` — generated on demand when you want a quick Plotly
  validation overlay

### 1. Regenerate the example data

```bash
uv run poe generate-examples
```

### 2. Run a fit from the CLI

```bash
uv run spectrafit fit examples/basic/input.toml --noplot
uv run spectrafit fit examples/two-peak-constrained/input.toml --noplot
```

### 3. Open an example notebook directly

```bash
jupyter lab examples/basic/notebook.ipynb
jupyter lab examples/two-peak-constrained/notebook.ipynb
```

For the repository examples, opening the committed notebook file directly is the
recommended path. You do not need a special launcher to explore the local
example workflow.

## What gets written where

The example workflows keep persistent artifacts next to the example so a
scientist can inspect results without guessing where files went.

| Surface | Example path | Typical artifacts |
|---------|--------------|-------------------|
| CLI live workflow | `examples/<name>/outputs/live/cli/` | `input.resolved.json`, `<name>_fit.csv`, `<name>_components.csv`, `<name>_correlation.csv`, `<name>_summary.json` |
| Notebook live workflow | `examples/<name>/outputs/live/notebook/` | `fit_<name>.csv`, `metric_<name>.csv`, `peaks_<name>.csv`, `<name>.lock` |

Two concrete directories to inspect after a run are:

- `examples/basic/outputs/live/cli/`
- `examples/basic/outputs/live/notebook/`

## Example workflows for scientists

### `basic/`

- Purpose: learn the smallest useful v2 fit
- Models: one Gaussian peak + flat linear background
- Best for: first-time users learning the TOML schema and output files
- Read more: [`examples/basic/README.md`](examples/basic/README.md)

### `two-peak-constrained/`

- Purpose: fit overlapping peaks with physically meaningful constraints
- Models: Gaussian + Pseudo-Voigt + linear background
- Best for: learning dot-notation constraints such as `p1.center + 1.0`
- Read more:
  [`examples/two-peak-constrained/README.md`](examples/two-peak-constrained/README.md)

## Focused validation commands

```bash
uv run poe validate-examples      # pipeline smoke tests for examples/*
uv run poe validate-cli-examples  # verify CLI exports for committed examples
uv run poe live                   # regenerate data and refresh CLI + notebook live outputs
```

## Command-line usage

The public fitting command is:

```bash
uv run spectrafit fit [CONFIG] [--noplot] [--outfile NAME]
```

Use `uv run spectrafit fit --help` to see the full current CLI contract.

## Jupyter usage

The shipped example notebooks demonstrate the canonical notebook flow:

1. Load local data through `spectrafit.notebook.read(...)`
2. Define peaks/background with compact `sf.peak(...)` and `sf.background(...)`
3. Run `spectrafit.notebook.fit(...)` and export persistent artifacts into
   `outputs/live/notebook/`

If you want a reusable notebook-oriented environment inside the repo, install
the `jupyter` extra and open the example notebook you care about with
`jupyter lab <path-to-notebook>`.

## Documentation

Please see the [extended documentation](https://anselmoo.github.io/spectrafit/)
for the full usage of `SpectraFit`.

The documentation is generated by
<a href="https://squidfunk.github.io/mkdocs-material/">
<img src="https://img.shields.io/badge/Material_for_MkDocs-526CFE?style=for-the-badge&logo=MaterialForMkDocs&logoColor=white" alt="Built with Material for MkDocs" style="vertical-align: middle; height: 20px;">
</a>.
