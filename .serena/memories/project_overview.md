# SpectraFit – Project Overview

## Purpose
Fast fitting of 2D- and 3D-Spectra using `lmfit`. Supports Gaussian, Lorentzian, Voigt, PseudoVoigt, Pearson, step-functions, polynomials and more. CLI-first; also usable as a Python API / Jupyter notebook plugin.

## Current version
1.4.1 (migrating to 2.0.0 on branch `v2.0.0`)

## Tech Stack
| Layer | Libraries |
|-------|-----------|
| Fitting engine | lmfit, scipy, numpy |
| Data models | pydantic v2 |
| CLI | typer |
| Data handling | pandas |
| Reporting | tabulate, seaborn |
| Package management | uv |
| Build backend | hatchling |
| Python versions | 3.10 – 3.13 |

## Entry Points
- `spectrafit` → `spectrafit.cli.main:run`
- `spectrafit-jupyter` → `spectrafit.app.app:jupyter`
- Plugin entry-points: `[project.entry-points."spectrafit.plugins"]`

## Repository
https://github.com/Anselmoo/spectrafit
