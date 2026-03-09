"""Notebook template builder for ``spectrafit init --jupyter``.

Generates a ``spectrafit_getting_started.ipynb`` notebook with two sections:

1. **Synthetic RIXS demo** — fit a Gaussian + Lorentzian pair to synthetic data.
2. **Bring-your-own-data** — commented-out template cells for real measurements.
"""

from __future__ import annotations

import json

from pathlib import Path  # noqa: TC003


# ---------------------------------------------------------------------------
# Notebook cell helpers (pure strings — no nbformat dependency at import time)
# ---------------------------------------------------------------------------

_HEADER_MD = """\
# SpectraFit — Getting Started

Welcome to **SpectraFit** 🎉
This notebook walks you through a complete spectral fitting workflow.

## Contents
1. [Synthetic demo fit](#1-Synthetic-demo-fit)
2. [Fit your own data](#2-Fit-your-own-data)

> **Tip:** run each cell with `Shift+Enter`.
"""

_IMPORTS_CODE = """\
from __future__ import annotations

import numpy as np
import pandas as pd
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.jupyter.core import SpectraFitNotebook
"""

_SYNTH_DATA_CODE = """\
# --- Section 1: Synthetic demo fit ---
rng = np.random.default_rng(42)
x = np.linspace(-5, 5, 200)
y = (
    0.8 * np.exp(-0.5 * ((x - 0.5) / 0.4) ** 2)   # gaussian
    + 0.5 / (1 + ((x + 1.0) / 0.3) ** 2)           # lorentzian
    + 0.02 * rng.standard_normal(len(x))            # noise
)
df = pd.DataFrame({"energy": x, "intensity": y})
df.head()
"""

_FIT_CONFIG_CODE = """\
# v2 format: flat ``components`` list (maps to [[components]] TOML syntax).
# Each component has an id, model name, and typed parameter bounds.
config = {
    "components": [
        {
            "id": "p1",
            "model": "pseudovoigt",
            "parameters": {
                "amplitude": {"min": 0.0, "max": 2.0, "vary": True, "value": 0.8},
                "center":    {"min": -3.0, "max": 3.0, "vary": True, "value": 0.5},
                "fwhmg":     {"min": 0.05, "max": 2.0, "vary": True, "value": 0.4},
                "fwhml":     {"min": 0.05, "max": 2.0, "vary": True, "value": 0.3},
            },
        },
        {
            "id": "p2",
            "model": "lorentzian",
            "parameters": {
                "amplitude": {"min": 0.0, "max": 2.0, "vary": True, "value": 0.5},
                "center":    {"min": -3.0, "max": 3.0, "vary": True, "value": -1.0},
                "fwhml":     {"min": 0.05, "max": 2.0, "vary": True, "value": 0.3},
            },
        },
    ],
    "minimizer": {"nan_policy": "propagate"},
    "optimizer": {"max_nfev": 2000, "method": "leastsq"},
}
"""

_FIT_RUN_CODE = """\
cfg = UnifiedFittingConfig.from_dict(config)
sfn = SpectraFitNotebook.from_config(df=df, config=cfg)
sfn.solver_fitting()
sfn.display_fit()
"""

_OWN_DATA_MD = """\
## 2 — Fit your own data

Replace `your_data.csv` with the path to your measurement file.
Adjust the peak model and initial parameters to match your spectrum.
"""

_OWN_DATA_CODE = """\
# Uncomment and edit to load your own data:
# df_real = pd.read_csv("your_data.csv")
# df_real.columns = ["energy", "intensity"]  # rename as needed

# config_real = {
#     "components": [
#         {
#             "id": "p1",
#             "model": "gaussian",
#             "parameters": {
#                 "amplitude": {"min": 0.0, "max": 10.0, "vary": True, "value": 1.0},
#                 "center": {"min": -10.0, "max": 10.0, "vary": True, "value": 0.0},
#                 "fwhmg": {"min": 0.01, "max": 5.0, "vary": True, "value": 0.5},
#             },
#         }
#     ],
#     "minimizer": {"nan_policy": "propagate"},
#     "optimizer": {"max_nfev": 5000, "method": "leastsq"},
# }
# cfg_real = UnifiedFittingConfig.from_dict(config_real)
# sfn_real = SpectraFitNotebook.from_config(df=df_real, config=cfg_real)
# sfn_real.solver_fitting()
# sfn_real.display_fit()
"""


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------


def build_starter_notebook(project_name: str) -> dict[str, object]:
    """Build a *Getting Started* notebook as a raw nbformat dict.

    Args:
        project_name: Name of the project — used in the first cell heading.

    Returns:
        Dict representing an nbformat v4 notebook (ready for ``json.dumps``).
    """

    def md(source: str) -> dict[str, object]:
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": source,
        }

    def code(source: str) -> dict[str, object]:
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": source,
        }

    cells: list[dict[str, object]] = [
        md(
            f"# {project_name} — SpectraFit Getting Started\n\n"
            + _HEADER_MD[_HEADER_MD.find("\n") + 1 :]
        ),
        code(_IMPORTS_CODE),
        md("## 1 — Synthetic demo fit"),
        code(_SYNTH_DATA_CODE),
        code(_FIT_CONFIG_CODE),
        code(_FIT_RUN_CODE),
        md(_OWN_DATA_MD),
        code(_OWN_DATA_CODE),
    ]

    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10.0",
            },
            "spectrafit": {"project": project_name},
        },
        "cells": cells,
    }


def write_starter_notebook(project_name: str, output_path: Path) -> None:
    """Serialise the starter notebook to *output_path*.

    Args:
        project_name: Name of the project for the notebook title.
        output_path: Destination ``.ipynb`` file path.
    """
    nb = build_starter_notebook(project_name)
    output_path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
