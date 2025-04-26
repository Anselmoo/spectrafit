---
title: Installation Guide
description: How to install SpectraFit and its dependencies using different methods
tags:
  - installation
  - dependencies
  - python
  - uv
  - pip
  - conda
---

# Installation

SpectraFit is available as a Python package and can be installed using various package managers. The recommended Python version is 3.8 or higher.

## Quick Install Using UV

[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver that we recommend for installing SpectraFit:

```bash
uv pip install spectrafit
```

## Standard Installation Using pip

You can install SpectraFit using pip, which is the standard package manager for Python:

```bash
pip install spectrafit
```

## Development Installation

If you want to contribute to SpectraFit or install the latest development version, you can install directly from the GitHub repository:

```bash
# Install using UV (recommended)
uv pip install git+https://github.com/Anselmoo/spectrafit.git

# Or using pip
pip install git+https://github.com/Anselmoo/spectrafit.git
```

For a development setup with all dependencies:

```bash
# Clone the repository
git clone https://github.com/Anselmoo/spectrafit.git
cd spectrafit

# Install with development dependencies using UV
uv pip install -e ".[dev]"

# Setup pre-commit hooks for development
pre-commit install --install-hooks
```

## Installation with Extra Features

SpectraFit supports optional dependencies for additional features:

```bash
# Install with all extras
uv pip install "spectrafit[all]"

# Install with specific extras
uv pip install "spectrafit[plotting,jupyter]"
```

Available extras include:

- `plotting`: For enhanced visualization capabilities
- `jupyter`: For Jupyter notebook integration
- `dev`: For development dependencies (testing, linting, etc.)
- `all`: Installs all optional dependencies

## Conda Installation

If you prefer using conda for managing Python environments, you can create a dedicated environment for SpectraFit:

```bash
# Create a new conda environment
conda create -n spectrafit python=3.10
conda activate spectrafit

# Install using pip within conda
pip install spectrafit
```

## Verification

After installation, you can verify that SpectraFit is correctly installed by running:

```bash
spectrafit --version
```

## System Requirements

- **Python**: 3.8 or higher
- **OS**: Windows, macOS, or Linux
- **Dependencies**: All dependencies will be automatically installed with the package

For more details on dependencies, see the `pyproject.toml` file in the repository.

## Troubleshooting

If you encounter any issues during installation:

1. Make sure your Python version is 3.8 or higher
2. Try upgrading your package manager: `uv pip install --upgrade pip` or `pip install --upgrade pip`
3. For conda environments, ensure conda-forge is in your channels: `conda config --add channels conda-forge`
4. Check the [GitHub Issues](https://github.com/Anselmoo/spectrafit/issues) for known problems
5. Report new issues on the [GitHub repository](https://github.com/Anselmoo/spectrafit/issues)
